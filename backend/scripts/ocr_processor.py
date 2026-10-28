"""CPU PaddleOCR runner. Input/output files are private temporary files owned by worker.
Never prints document contents. Run using the isolated requirements-ocr.txt environment.
"""
import argparse,json,os,time,warnings
from pathlib import Path
os.environ.setdefault('PADDLE_PDX_MODEL_SOURCE','BOS')
os.environ.setdefault('PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK','True')
os.environ.setdefault('OMP_NUM_THREADS','1')
cache=Path(__file__).resolve().parents[1]/'.ocr-models'
os.environ.setdefault('PADDLE_PDX_CACHE_HOME',str(cache/'paddlex'))
os.environ.setdefault('HF_HOME',str(cache/'huggingface'))
os.environ.setdefault('MODELSCOPE_CACHE',str(cache/'modelscope'))
MAX_PAGES=5
MAX_PIXELS=16_000_000
MAX_TEXT=40000
RECOGNITION_MODELS={
    'hi':'devanagari','mr':'devanagari','ne':'devanagari','sa':'devanagari',
    'en':'en','ta':'ta','te':'te','ur':'arabic','ar':'arabic',
    'fr':'latin','de':'latin','es':'latin','pt':'latin','ru':'eslav',
}


def images(path):
    from PIL import Image,ImageOps
    Image.MAX_IMAGE_PIXELS=MAX_PIXELS
    if path.suffix.lower()=='.pdf':
        import pypdfium2 as pdfium
        try:document=pdfium.PdfDocument(str(path))
        except Exception:raise ValueError('invalid_document') from None
        try:
            if len(document)>MAX_PAGES:raise ValueError('too_many_pages')
            for index in range(len(document)):
                page=document[index]
                try:
                    width,height=page.get_size();scale=min(2.0,(MAX_PIXELS/max(1,width*height))**0.5)
                    bitmap=page.render(scale=scale)
                    try:yield bitmap.to_pil().convert('RGB').copy()
                    finally:bitmap.close()
                finally:page.close()
        finally:document.close()
    else:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('error',Image.DecompressionBombWarning)
                with Image.open(path) as image:
                    if image.width*image.height>MAX_PIXELS:raise ValueError('image_too_large')
                    image.load();yield ImageOps.exif_transpose(image).convert('RGB')
        except (Image.DecompressionBombError,Image.DecompressionBombWarning):raise ValueError('image_too_large') from None


def extract(path,language):
    from paddleocr import PaddleOCR
    import numpy as np
    recognition=RECOGNITION_MODELS[language]+'_PP-OCRv5_mobile_rec'
    engine=PaddleOCR(device='cpu',text_detection_model_name='PP-OCRv5_mobile_det',text_recognition_model_name=recognition,
        use_doc_orientation_classify=False,use_doc_unwarping=False,use_textline_orientation=False,
        enable_mkldnn=False,cpu_threads=1,text_det_limit_side_len=960,text_det_limit_type='max')
    pages=[];total=0
    for number,image in enumerate(images(path),1):
        try:
            lines=[]
            for prediction in engine.predict(np.asarray(image)):
                data=prediction.json
                if callable(data):data=data()
                if isinstance(data,str):data=json.loads(data)
                data=data.get('res',data)
                texts=data.get('rec_texts',[]);scores=data.get('rec_scores',[])
                for index,text in enumerate(texts):
                    text=str(text).strip()
                    if not text:continue
                    total+=len(text)+1
                    if total>MAX_TEXT:raise ValueError('text_too_large')
                    lines.append(dict(text=text,confidence=round(float(scores[index]),4) if index<len(scores) else None))
            pages.append(dict(page=number,text='\n'.join(line['text'] for line in lines),lines=lines))
        finally:image.close()
    return pages


class TranslationTooLong(Exception):pass


def translation_chunks(text,limit=450):
    # MyMemory limits q to 500 UTF-8 bytes, not 500 Unicode characters.
    import re
    chunks=[];current=''
    for word in re.findall(r'\S+\s*|\s+',text):
        if len(word.encode('utf-8'))>limit:
            if current.strip():chunks.append(current.strip());current=''
            for character in word:
                if len((current+character).encode('utf-8'))>limit:
                    chunks.append(current.strip());current=''
                current+=character
        elif len((current+word).encode('utf-8'))>limit:
            if current.strip():chunks.append(current.strip())
            current=word
        else:current+=word
    if current.strip():chunks.append(current.strip())
    return chunks


def translate(text,language):
    from deep_translator import MyMemoryTranslator
    from deep_translator.constants import BASE_URLS
    from deep_translator.exceptions import TooManyRequests
    import requests
    from urllib.parse import urlsplit
    codes={'hi':'hi-IN','mr':'mr-IN','ne':'ne-NP','sa':'sa-IN','ta':'ta-IN','te':'te-IN',
        'ur':'ur-PK','ar':'ar-SA','fr':'fr-FR','de':'de-DE','es':'es-ES','pt':'pt-PT','ru':'ru-RU'}
    if len(text)>4000:raise TranslationTooLong()
    # deep-translator 1.11 defaults MyMemory to HTTP; always use verified HTTPS.
    BASE_URLS['MYMEMORY']='https://api.mymemory.translated.net/get'
    original=requests.get
    def bounded(url,*args,**kwargs):
        parts=urlsplit(url)
        if parts.scheme!='https' or parts.hostname!='api.mymemory.translated.net' or parts.path!='/get':
            raise RuntimeError('translation_provider_not_allowed')
        kwargs['timeout']=15;kwargs['allow_redirects']=False
        response=original(url,*args,**kwargs)
        try:
            data=response.json() if response.status_code==200 else {}
            if response.status_code==429 or str(data.get('responseStatus'))=='429' or data.get('quotaFinished'):
                raise TooManyRequests()
            if response.status_code!=200 or str(data.get('responseStatus'))!='200':
                raise RuntimeError('translation_unavailable')
        except Exception:
            response.close();raise
        return response
    requests.get=bounded
    try:
        translator=MyMemoryTranslator(source=codes[language],target='en-GB')
        translated=[]
        for index,chunk in enumerate(translation_chunks(text)):
            if index:time.sleep(0.3)
            translated.append(translator.translate(chunk))
        return '\n'.join(translated)
    finally:requests.get=original


def process(path,language,wants_translation):
    pages=extract(path,language);text='\n\n'.join(page['text'] for page in pages).strip()
    result=dict(engine='PaddleOCR',source_language=language,page_count=len(pages),pages=pages,original_text=text,english_text=None,
        translation_status='NOT_REQUESTED',warnings=['Machine-extracted text and translation can contain errors. Verify names, medicine doses, dates and units against the original report.'])
    if not text:
        result['warnings'].append('No readable text found. Try a clearer printed scan; handwriting may not be recognized.')
        result['translation_status']='NO_TEXT'
    elif wants_translation:
        if language=='en':result.update(english_text=text,translation_status='COMPLETED')
        else:
            try:result.update(english_text=translate(text,language),translation_status='COMPLETED',translation_provider='MyMemory via deep-translator')
            except Exception as error:
                result['translation_status']='FAILED'
                limited=type(error).__name__=='TooManyRequests'
                message='MyMemory free translation quota is temporarily unavailable. Original text is retained; wait before retrying.' if limited else 'Free translation supports reports up to 4000 characters. Original text is retained; split the document for translation.' if type(error).__name__=='TranslationTooLong' else 'English translation failed. Original extracted text is retained; retry if desired.'
                result['translation_error']=dict(code='translation_rate_limited' if limited else 'translation_too_long' if type(error).__name__=='TranslationTooLong' else 'translation_unavailable',message=message)
                result['warnings'].append(message)
    return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('input');parser.add_argument('output');parser.add_argument('language');parser.add_argument('--translate',action='store_true');args=parser.parse_args()
    try:result=process(Path(args.input),args.language,args.translate)
    except ValueError as error:result={'error':str(error) if str(error) in ('invalid_document','too_many_pages','image_too_large','text_too_large') else 'processing_failed'}
    except Exception:result={'error':'processing_failed'}
    Path(args.output).write_text(json.dumps(result,ensure_ascii=False),encoding='utf-8')

if __name__=='__main__':main()
