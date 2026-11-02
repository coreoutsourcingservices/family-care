import {Link} from 'react-router-dom';
export default function AccessApprovals(){return <section className="family-access-panel"><h1>Family invitations</h1><p>Invite a member from their care area.</p><Link to="/customer/adult?add=1">Add an adult member</Link><br/><Link to="/customer/women?add=1">Add a women?s health member</Link></section>;}
