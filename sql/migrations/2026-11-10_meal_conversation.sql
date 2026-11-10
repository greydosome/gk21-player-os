BEGIN;
CREATE TABLE IF NOT EXISTS meal_conversation_event (
 conversation_id text NOT NULL, message_id text NOT NULL, meal_key text NOT NULL,
 payload jsonb NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(conversation_id,message_id,meal_key)
);
CREATE TABLE IF NOT EXISTS meal_conversation_entry (
 conversation_id text NOT NULL, meal_key text NOT NULL,
 record_date date NOT NULL, revision integer NOT NULL CHECK(revision>0),
 deleted boolean NOT NULL DEFAULT false, payload jsonb NOT NULL,
 updated_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(conversation_id,meal_key)
);
CREATE INDEX IF NOT EXISTS meal_conversation_day ON meal_conversation_entry(record_date);
COMMIT;
