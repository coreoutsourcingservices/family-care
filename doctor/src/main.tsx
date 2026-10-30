// Shared router and UI shell; doctor-owned pages/components remain under doctor/src.
if (window.location.pathname === '/') {
  window.history.replaceState(null, '', '/doctor/login');
}
void import('../../app/src/main');