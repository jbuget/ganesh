-- La base de test vit a cote de la base de travail : `make test` la migre puis
-- la vide a chaque session, sans jamais toucher aux donnees de developpement.
CREATE DATABASE timesheet_test OWNER timesheet;
