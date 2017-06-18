SET SYNCHRONOUS_COMMIT = 'off';

CREATE EXTENSION IF NOT EXISTS citext;

--

DROP TABLE IF EXISTS users CASCADE;

CREATE TABLE IF NOT EXISTS users (
  id       SERIAL PRIMARY KEY,
  about    TEXT DEFAULT NULL,
  email    citext UNIQUE,
  fullname TEXT DEFAULT NULL,
  nickname citext COLLATE ucs_basic UNIQUE
);

--

DROP TABLE IF EXISTS forums CASCADE;

CREATE TABLE IF NOT EXISTS forums (
  "user"  citext REFERENCES users (nickname) ON DELETE CASCADE  NOT NULL,
  posts   INTEGER DEFAULT 0,
  threads INTEGER DEFAULT 0,
  slug    citext UNIQUE                                         NOT NULL,
  title   TEXT                                                  NOT NULL
);

--

DROP TABLE IF EXISTS threads CASCADE;

CREATE TABLE IF NOT EXISTS threads (
  author  citext REFERENCES users (nickname) ON DELETE CASCADE  NOT NULL,
  created TIMESTAMPTZ DEFAULT NOW(),
  forum   citext REFERENCES forums (slug) ON DELETE CASCADE     NOT NULL,
  id      SERIAL PRIMARY KEY,
  message TEXT        DEFAULT NULL,
  slug    citext UNIQUE,
  title   TEXT                                                  NOT NULL,
  votes   INTEGER     DEFAULT 0
);

--

DROP TABLE IF EXISTS posts CASCADE;

CREATE TABLE IF NOT EXISTS posts (
  author   citext REFERENCES users (nickname) ON DELETE CASCADE      NOT NULL,
  created  TIMESTAMPTZ DEFAULT NOW(),
  forum    citext REFERENCES forums (slug) ON DELETE CASCADE         NOT NULL,
  id       SERIAL PRIMARY KEY,
  isEdited BOOLEAN     DEFAULT FALSE,
  message  TEXT        DEFAULT NULL,
  parent   INTEGER     DEFAULT 0,
  thread   INTEGER REFERENCES threads (id) ON DELETE CASCADE         NOT NULL,
  path     INTEGER [],
  root_id  INTEGER
);

--

DROP TABLE IF EXISTS forum_users CASCADE;

CREATE TABLE IF NOT EXISTS forum_users (
  user_id INTEGER REFERENCES users (id) ON DELETE CASCADE,
  forum   citext REFERENCES forums (slug) ON DELETE CASCADE
);

--

DROP TABLE IF EXISTS votes CASCADE;

CREATE TABLE IF NOT EXISTS votes (
  nickname citext REFERENCES users (nickname) ON DELETE CASCADE,
  thread   INTEGER REFERENCES threads (id) ON DELETE CASCADE,
  voice    INTEGER DEFAULT 0,
  CONSTRAINT unique_pair UNIQUE (nickname, thread)
);

--

DROP INDEX IF EXISTS user_nickname_forums_idx;

CREATE INDEX IF NOT EXISTS user_nickname_forums_idx
  ON forums ("user");

--

DROP INDEX IF EXISTS author_threads_idx;
DROP INDEX IF EXISTS forum_slug_threads_idx;

CREATE INDEX IF NOT EXISTS author_threads_idx
  ON threads (author);
CREATE INDEX IF NOT EXISTS forum_threads_idx
  ON threads (forum);

--

DROP INDEX IF EXISTS author_posts_idx;
DROP INDEX IF EXISTS forum_posts_idx;
DROP INDEX IF EXISTS flat_sort_posts_idx;
DROP INDEX IF EXISTS tree_sort_posts_idx;
DROP INDEX IF EXISTS parent_tree_sort_posts_idx;
DROP INDEX IF EXISTS parent_tree_sort_posts_sub_idx;

CREATE INDEX IF NOT EXISTS author_posts_idx
  ON posts (author);
CREATE INDEX IF NOT EXISTS forum_posts_idx
  ON posts (forum);
CREATE INDEX IF NOT EXISTS flat_sort_posts_idx
  ON posts (thread, created, id);
CREATE INDEX IF NOT EXISTS tree_sort_posts_idx
  ON posts (thread, path);
CREATE INDEX IF NOT EXISTS parent_tree_sort_posts_idx
  ON posts (root_id, path);
CREATE INDEX IF NOT EXISTS parent_tree_sort_posts_sub_idx
  ON posts (thread, parent, id);

--

DROP INDEX IF EXISTS user_id_forum_users_idx;
DROP INDEX IF EXISTS forum_forum_users_idx;

CREATE INDEX IF NOT EXISTS user_id_forum_users_idx
  ON forum_users (user_id);
CREATE INDEX IF NOT EXISTS forum_forum_users_idx
  ON forum_users (forum);

--

CREATE OR REPLACE FUNCTION after_thread_insert()
  RETURNS TRIGGER AS $$
BEGIN
  UPDATE forums
  SET threads = threads + 1
  WHERE slug = NEW.forum;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_threads_count_trigger
AFTER INSERT ON threads
FOR EACH ROW EXECUTE PROCEDURE after_thread_insert();

CREATE OR REPLACE FUNCTION on_insert_post_or_thread()
  RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO forum_users (user_id, forum) VALUES ((SELECT id
                                                     FROM users
                                                     WHERE nickname = NEW.author), NEW.forum);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER post_insert_trigger
AFTER INSERT ON posts
FOR EACH ROW EXECUTE PROCEDURE on_insert_post_or_thread();

CREATE TRIGGER thread_insert_trigger
AFTER INSERT ON threads
FOR EACH ROW EXECUTE PROCEDURE on_insert_post_or_thread();

--

DROP FUNCTION IF EXISTS update_or_insert_votes( citext, INTEGER, INTEGER );

CREATE OR REPLACE FUNCTION update_or_insert_votes(vote_user_nickname citext, vote_thread INTEGER,
                                                  vote_value         INTEGER)
  RETURNS VOID AS $$
BEGIN
  INSERT INTO votes (nickname, thread, voice) VALUES (vote_user_nickname, vote_thread, vote_value)
  ON CONFLICT (nickname, thread)
    DO UPDATE SET voice = vote_value;
  UPDATE threads
  SET votes = (SELECT SUM(voice)
               FROM votes
               WHERE thread = vote_thread)
  WHERE id = vote_thread;
END;
$$ LANGUAGE plpgsql;