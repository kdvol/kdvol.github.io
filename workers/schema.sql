create table if not exists reactions (
  story text not null,
  emoji text not null,
  count integer not null default 0,
  primary key (story, emoji)
);
create index if not exists idx_reactions_story on reactions(story);
