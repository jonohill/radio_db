--
-- PostgreSQL database dump
--

-- Dumped from database version 13.4 (Debian 13.4-4.pgdg110+1)
-- Dumped by pg_dump version 13.4 (Debian 13.4-4.pgdg110+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: playlisttype; Type: TYPE; Schema: public; Owner: radio_db
--

CREATE TYPE public.playlisttype AS ENUM (
    'Top'
);


ALTER TYPE public.playlisttype OWNER TO radio_db;

--
-- Name: statekey; Type: TYPE; Schema: public; Owner: radio_db
--

CREATE TYPE public.statekey AS ENUM (
    'SpotifyAuth'
);


ALTER TYPE public.statekey OWNER TO radio_db;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: radio_db
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO radio_db;

--
-- Name: pending; Type: TABLE; Schema: public; Owner: radio_db
--

CREATE TABLE public.pending (
    id bigint NOT NULL,
    station bigint,
    artist character varying,
    title character varying,
    seen_at timestamp without time zone,
    picked_at timestamp without time zone
);


ALTER TABLE public.pending OWNER TO radio_db;

--
-- Name: pending_id_seq; Type: SEQUENCE; Schema: public; Owner: radio_db
--

CREATE SEQUENCE public.pending_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.pending_id_seq OWNER TO radio_db;

--
-- Name: pending_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: radio_db
--

ALTER SEQUENCE public.pending_id_seq OWNED BY public.pending.id;


--
-- Name: play; Type: TABLE; Schema: public; Owner: radio_db
--

CREATE TABLE public.play (
    id bigint NOT NULL,
    station bigint,
    song bigint,
    at timestamp without time zone NOT NULL
);


ALTER TABLE public.play OWNER TO radio_db;

--
-- Name: play_id_seq; Type: SEQUENCE; Schema: public; Owner: radio_db
--

CREATE SEQUENCE public.play_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.play_id_seq OWNER TO radio_db;

--
-- Name: play_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: radio_db
--

ALTER SEQUENCE public.play_id_seq OWNED BY public.play.id;


--
-- Name: playlist; Type: TABLE; Schema: public; Owner: radio_db
--

CREATE TABLE public.playlist (
    id bigint NOT NULL,
    station bigint,
    type_ public.playlisttype,
    spotify_uri character varying
);


ALTER TABLE public.playlist OWNER TO radio_db;

--
-- Name: playlist_id_seq; Type: SEQUENCE; Schema: public; Owner: radio_db
--

CREATE SEQUENCE public.playlist_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.playlist_id_seq OWNER TO radio_db;

--
-- Name: playlist_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: radio_db
--

ALTER SEQUENCE public.playlist_id_seq OWNED BY public.playlist.id;


--
-- Name: song; Type: TABLE; Schema: public; Owner: radio_db
--

CREATE TABLE public.song (
    id bigint NOT NULL,
    key bigint NOT NULL,
    artist character varying NOT NULL,
    title character varying NOT NULL,
    spotify_uri character varying
);


ALTER TABLE public.song OWNER TO radio_db;

--
-- Name: song_id_seq; Type: SEQUENCE; Schema: public; Owner: radio_db
--

CREATE SEQUENCE public.song_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.song_id_seq OWNER TO radio_db;

--
-- Name: song_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: radio_db
--

ALTER SEQUENCE public.song_id_seq OWNED BY public.song.id;


--
-- Name: state; Type: TABLE; Schema: public; Owner: radio_db
--

CREATE TABLE public.state (
    key public.statekey NOT NULL,
    value character varying
);


ALTER TABLE public.state OWNER TO radio_db;

--
-- Name: station; Type: TABLE; Schema: public; Owner: radio_db
--

CREATE TABLE public.station (
    id bigint NOT NULL,
    key character varying,
    name character varying NOT NULL,
    url character varying NOT NULL
);


ALTER TABLE public.station OWNER TO radio_db;

--
-- Name: station_id_seq; Type: SEQUENCE; Schema: public; Owner: radio_db
--

CREATE SEQUENCE public.station_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.station_id_seq OWNER TO radio_db;

--
-- Name: station_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: radio_db
--

ALTER SEQUENCE public.station_id_seq OWNED BY public.station.id;


--
-- Name: pending id; Type: DEFAULT; Schema: public; Owner: radio_db
--

ALTER TABLE ONLY public.pending ALTER COLUMN id SET DEFAULT nextval('public.pending_id_seq'::regclass);


--
-- Name: play id; Type: DEFAULT; Schema: public; Owner: radio_db
--

ALTER TABLE ONLY public.play ALTER COLUMN id SET DEFAULT nextval('public.play_id_seq'::regclass);


--
-- Name: playlist id; Type: DEFAULT; Schema: public; Owner: radio_db
--

ALTER TABLE ONLY public.playlist ALTER COLUMN id SET DEFAULT nextval('public.playlist_id_seq'::regclass);


--
-- Name: song id; Type: DEFAULT; Schema: public; Owner: radio_db
--

ALTER TABLE ONLY public.song ALTER COLUMN id SET DEFAULT nextval('public.song_id_seq'::regclass);


--
-- Name: station id; Type: DEFAULT; Schema: public; Owner: radio_db
--

ALTER TABLE ONLY public.station ALTER COLUMN id SET DEFAULT nextval('public.station_id_seq'::regclass);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: radio_db
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: pending pending_pkey; Type: CONSTRAINT; Schema: public; Owner: radio_db
--

ALTER TABLE ONLY public.pending
    ADD CONSTRAINT pending_pkey PRIMARY KEY (id);


--
-- Name: play play_pkey; Type: CONSTRAINT; Schema: public; Owner: radio_db
--

ALTER TABLE ONLY public.play
    ADD CONSTRAINT play_pkey PRIMARY KEY (id);


--
-- Name: playlist playlist_pkey; Type: CONSTRAINT; Schema: public; Owner: radio_db
--

ALTER TABLE ONLY public.playlist
    ADD CONSTRAINT playlist_pkey PRIMARY KEY (id);


--
-- Name: playlist playlist_spotify_uri_key; Type: CONSTRAINT; Schema: public; Owner: radio_db
--

ALTER TABLE ONLY public.playlist
    ADD CONSTRAINT playlist_spotify_uri_key UNIQUE (spotify_uri);


--
-- Name: song song_key_key; Type: CONSTRAINT; Schema: public; Owner: radio_db
--

ALTER TABLE ONLY public.song
    ADD CONSTRAINT song_key_key UNIQUE (key);


--
-- Name: song song_pkey; Type: CONSTRAINT; Schema: public; Owner: radio_db
--

ALTER TABLE ONLY public.song
    ADD CONSTRAINT song_pkey PRIMARY KEY (id);


--
-- Name: song song_spotify_uri_key; Type: CONSTRAINT; Schema: public; Owner: radio_db
--

ALTER TABLE ONLY public.song
    ADD CONSTRAINT song_spotify_uri_key UNIQUE (spotify_uri);


--
-- Name: state state_pkey; Type: CONSTRAINT; Schema: public; Owner: radio_db
--

ALTER TABLE ONLY public.state
    ADD CONSTRAINT state_pkey PRIMARY KEY (key);


--
-- Name: station station_key_key; Type: CONSTRAINT; Schema: public; Owner: radio_db
--

ALTER TABLE ONLY public.station
    ADD CONSTRAINT station_key_key UNIQUE (key);


--
-- Name: station station_pkey; Type: CONSTRAINT; Schema: public; Owner: radio_db
--

ALTER TABLE ONLY public.station
    ADD CONSTRAINT station_pkey PRIMARY KEY (id);


--
-- Name: artist_title_index; Type: INDEX; Schema: public; Owner: radio_db
--

CREATE UNIQUE INDEX artist_title_index ON public.song USING btree (artist, title);


--
-- Name: pending pending_station_fkey; Type: FK CONSTRAINT; Schema: public; Owner: radio_db
--

ALTER TABLE ONLY public.pending
    ADD CONSTRAINT pending_station_fkey FOREIGN KEY (station) REFERENCES public.station(id);


--
-- Name: play play_song_fkey; Type: FK CONSTRAINT; Schema: public; Owner: radio_db
--

ALTER TABLE ONLY public.play
    ADD CONSTRAINT play_song_fkey FOREIGN KEY (song) REFERENCES public.song(id);


--
-- Name: play play_station_fkey; Type: FK CONSTRAINT; Schema: public; Owner: radio_db
--

ALTER TABLE ONLY public.play
    ADD CONSTRAINT play_station_fkey FOREIGN KEY (station) REFERENCES public.station(id);


--
-- Name: playlist playlist_station_fkey; Type: FK CONSTRAINT; Schema: public; Owner: radio_db
--

ALTER TABLE ONLY public.playlist
    ADD CONSTRAINT playlist_station_fkey FOREIGN KEY (station) REFERENCES public.station(id);


--
-- PostgreSQL database dump complete
--