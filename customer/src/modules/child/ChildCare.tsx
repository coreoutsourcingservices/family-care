import MemberProfiles from '../../../../app/src/components/MemberProfiles';

export default function ChildCare({ accountId }: { accountId: string }) {
  return <MemberProfiles accountId={accountId} module="child" />;
}
