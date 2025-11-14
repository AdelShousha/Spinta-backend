# Model Changes Tracker

This document tracks database schema changes that need to be applied to SQLAlchemy models in `app/models/`.

---

## Match Model (`app/models/match.py`)

### Remove
```python
match_time = Column(Time, nullable=True)
is_home_match = Column(Boolean, nullable=False)
home_score = Column(Integer, nullable=True)
away_score = Column(Integer, nullable=True)
```

### Add
```python
our_score = Column(Integer, nullable=True)
opponent_score = Column(Integer, nullable=True)
result = Column(String(1), nullable=True)
```

---

## ClubSeasonStatistics Model (`app/models/club_season_statistics.py`)

### Add
```python
total_assists = Column(Integer, nullable=False, default=0)
team_form = Column(String(5), nullable=True)
```

---

## Goal Model (`app/models/goal.py`)

### Remove
```python
team_name = Column(String(255), nullable=False)
assist_name = Column(String(255), nullable=True)
period = Column(Integer, nullable=False)
goal_type = Column(String(50), nullable=True)
body_part = Column(String(50), nullable=True)
```

### Add
```python
is_our_goal = Column(Boolean, nullable=False)
```

---

## MatchLineup Model (`app/models/match_lineup.py`)

### Add New Model
```python
# Create new file: app/models/match_lineup.py

lineup_id = Column(GUID, primary_key=True, default=generate_uuid)
match_id = Column(GUID, ForeignKey("matches.match_id", ondelete="CASCADE"), nullable=False)
team_type = Column(String(20), nullable=False)  # 'our_team' or 'opponent_team'
player_id = Column(GUID, ForeignKey("players.player_id", ondelete="CASCADE"), nullable=True)
opponent_player_id = Column(GUID, ForeignKey("opponent_players.opponent_player_id", ondelete="CASCADE"), nullable=True)
player_name = Column(String(255), nullable=False)
jersey_number = Column(Integer, nullable=False)
position = Column(String(50), nullable=False)
created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
```

---

## Match Model (`app/models/match.py`)

### Add Relationship
```python
lineups = relationship("MatchLineup", back_populates="match", cascade="all, delete-orphan")
```

---
