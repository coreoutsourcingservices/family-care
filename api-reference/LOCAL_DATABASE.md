# Supabase connection troubleshooting

`MaxClientsInSessionMode` means the session pooler's client capacity is exhausted. It does not mean vaccine data was deleted or migrations are necessarily missing.

For a Supabase pooler URL, use the project's **transaction pooler** configuration (normally port `6543`) rather than holding session-mode connections on `5432`. Keep the same project credentials and TLS requirement. Obtain the exact connection string from the project's database settings; do not change the hostname or credentials blindly.

FamilyCare disables psycopg named prepared statements when the configured database port is `6543`, because transaction pooling can switch PostgreSQL server connections between transactions. Existing direct/session connections retain the default driver configuration.

After changing `backend/.env`, restart the backend. Check `/api/v1/health/ready`, then refresh the Vaccination page. Multiple readiness requests should all return HTTP 200. Avoid repeatedly starting backend processes against the same small database pool.

The vaccination UI displays **Unavailable** on an initial load failure, not fabricated zero counts. Refresh retries loading; later failures retain the last successfully loaded data alongside the error.

Publication is separate from connectivity. Imported UIP/IAP drafts remain drafts until actual medical review and administrator publication. Restoring the database connection does not approve or publish them.

Never commit `.env`, credentials or private backup files. The local connection change requires an environment update on other installations; a code push does not change their database configuration.
