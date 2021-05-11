most_played = """\
    select max(p.at), count(p.id), s.artist, s.title, s.spotify_uri from play p
    left join song s on s.id = p.song
    where p.at > (p.at - interval '7 days')
    group by s.id
    order by count(p.id), max(p.id) desc;
"""