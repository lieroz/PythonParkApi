SET SYNCHRONOUS_COMMIT = 'off';

CREATE EXTENSION IF NOT EXISTS CITEXT;

--

DROP TABLE IF EXISTS users CASCADE;

CREATE TABLE IF NOT EXISTS users (
  about    TEXT DEFAULT NULL,
  email    CITEXT UNIQUE,
  fullname TEXT DEFAULT NULL,
  nickname CITEXT COLLATE ucs_basic UNIQUE
);

--

DROP TABLE IF EXISTS forums CASCADE;

CREATE TABLE IF NOT EXISTS forums (
  "user"  CITEXT REFERENCES users (nickname) ON DELETE CASCADE  NOT NULL,
  posts   INTEGER DEFAULT 0,
  threads INTEGER DEFAULT 0,
  slug    CITEXT UNIQUE                                         NOT NULL,
  title   TEXT                                                  NOT NULL
);

--

DROP TABLE IF EXISTS threads CASCADE;

CREATE TABLE IF NOT EXISTS threads (
  author  CITEXT REFERENCES users (nickname) ON DELETE CASCADE  NOT NULL,
  created TIMESTAMPTZ DEFAULT NOW(),
  forum   CITEXT REFERENCES forums (slug) ON DELETE CASCADE     NOT NULL,
  id      SERIAL PRIMARY KEY,
  message TEXT        DEFAULT NULL,
  slug    CITEXT UNIQUE,
  title   TEXT                                                  NOT NULL,
  votes   INTEGER     DEFAULT 0
);

--

DROP TABLE IF EXISTS posts CASCADE;

CREATE TABLE IF NOT EXISTS posts (
  author    CITEXT REFERENCES users (nickname) ON DELETE CASCADE      NOT NULL,
  created   TIMESTAMPTZ DEFAULT NOW(),
  forum     CITEXT REFERENCES forums (slug) ON DELETE CASCADE         NOT NULL,
  id        SERIAL PRIMARY KEY,
  isEdited  BOOLEAN     DEFAULT FALSE,
  message   TEXT        DEFAULT NULL,
  parent    INTEGER     DEFAULT 0,
  thread_id INTEGER REFERENCES threads (id) ON DELETE CASCADE         NOT NULL,
  path      INTEGER [],
  root_id   INTEGER
);

--

DROP TABLE IF EXISTS forum_users CASCADE;

CREATE TABLE IF NOT EXISTS forum_users (
  nickname CITEXT REFERENCES users (nickname) ON DELETE CASCADE,
  forum    CITEXT REFERENCES forums (slug) ON DELETE CASCADE
);

--

DROP TABLE IF EXISTS votes CASCADE;

CREATE TABLE IF NOT EXISTS votes (
  nickname  CITEXT REFERENCES users (nickname) ON DELETE CASCADE,
  thread_id INTEGER REFERENCES threads (id) ON DELETE CASCADE,
  voice     INTEGER DEFAULT 0,
  CONSTRAINT unique_pair UNIQUE (nickname, thread_id)
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
  ON posts (thread_id, created, id);
CREATE INDEX IF NOT EXISTS tree_sort_posts_idx
  ON posts (thread_id, path);
CREATE INDEX IF NOT EXISTS parent_tree_sort_posts_idx
  ON posts (root_id, path);
CREATE INDEX IF NOT EXISTS parent_tree_sort_posts_sub_idx
  ON posts (thread_id, parent, id);

--

DROP INDEX IF EXISTS nickname_forum_users_idx;
DROP INDEX IF EXISTS forum_forum_users_idx;

CREATE INDEX IF NOT EXISTS nickname_forum_users_idx
  ON forum_users (nickname);
CREATE INDEX IF NOT EXISTS forum_forum_users_idx
  ON forum_users (forum);



CREATE OR REPLACE FUNCTION on_insert_post_or_thread()
  RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO forum_users (nickname, forum) VALUES (NEW.author, NEW.forum);
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

CREATE OR REPLACE FUNCTION update_or_insert_votes(vote_user_nickname INTEGER, vote_thread_id INTEGER,
                                                  vote_value         INTEGER)
  RETURNS VOID AS $$
BEGIN
  INSERT INTO votes (nickname, thread_id, voice) VALUES (vote_user_nickname, vote_thread_id, vote_value)
  ON CONFLICT (nickname, thread_id)
    DO UPDATE SET voice = vote_value;
  UPDATE threads
  SET votes = (SELECT SUM(voice)
               FROM votes
               WHERE thread_id = vote_thread_id)
  WHERE id = vote_thread_id;
END;
$$ LANGUAGE plpgsql;