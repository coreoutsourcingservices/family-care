import { Link } from "react-router-dom";
import {
  CreditCard,
  ShieldCheck,
  CalendarDays,
  Users,
  FileText,
} from "lucide-react";
import WorkspacePage from "../components/WorkspacePage";
import AgentBentoGrid, { FeatCard } from "../components/AgentBentoGrid";
import { getDoctorWorkspace } from "../onboarding/setupSession";
export default function Subscription() {
  const account = getDoctorWorkspace();
  return (
    <WorkspacePage
      title="Subscription"
      description="Your practice account and subscription details."
    >
      <section className="dr-subscription-hero">
        <span>
          <CreditCard size={30} />
        </span>
        <div>
          <small>YOUR PRACTICE ACCOUNT</small>
          <h2>{account?.user.full_name}</h2>
          <p>
            Subscription information has not been added to this account yet.
          </p>
        </div>
        <span className="dr-account-status">
          <ShieldCheck size={16} />
          {account?.user.approval_status === "APPROVED"
            ? "Verified doctor"
            : "Profile under review"}
        </span>
      </section>
      <AgentBentoGrid>
        <FeatCard
          title="Plan details"
          description="Your assigned subscription"
          tone="violet"
        >
          <div className="dr-subscription-status">
            <CreditCard />
            <strong>No plan assigned</strong>
            <p>No price or renewal date is available.</p>
          </div>
        </FeatCard>
        <FeatCard
          title="Practice access"
          description="Open your connected care workspace"
          tone="cyan"
        >
          <div className="dr-subscription-links">
            <Link to="/doctor/patients">
              <Users size={18} />
              Patients
            </Link>
            <Link to="/doctor/appointments">
              <CalendarDays size={18} />
              Appointments
            </Link>
            <Link to="/doctor/clinical-records">
              <FileText size={18} />
              Clinical records
            </Link>
          </div>
        </FeatCard>
      </AgentBentoGrid>
      <Link className="dw-secondary" to="/doctor/settings">
        Account settings
      </Link>
    </WorkspacePage>
  );
}
