import MemberProfiles from '../../components/MemberProfiles';

export default function AdultHealth({ accountId }: { accountId: string }) {
  return <MemberProfiles accountId={accountId} module="adult" />;
}
