import MemberProfiles from '../../components/MemberProfiles';

export default function WomenHealth({ accountId }: { accountId: string }) {
  return <MemberProfiles accountId={accountId} module="women" />;
}
