-- The test database lives beside the working one: `make test` migrates it then
-- empties it every session, never touching development data.
CREATE DATABASE timesheet_test OWNER timesheet;
