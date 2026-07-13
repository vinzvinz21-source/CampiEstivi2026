from alphaevolve.database import ProgramDatabase


def test_add_and_best_program():
    db = ProgramDatabase(num_islands=2, population_size=5)
    db.add("code_a", {"combined_score": 0.5}, generation=0, parent_id=None, island=0)
    db.add("code_b", {"combined_score": 0.9}, generation=1, parent_id=None, island=0)
    assert db.best_program.code == "code_b"


def test_population_size_capped_keeps_best():
    db = ProgramDatabase(num_islands=1, population_size=3)
    for i in range(10):
        db.add(f"code_{i}", {"combined_score": float(i)}, generation=i, parent_id=None, island=0)
    assert len(db._islands[0]) == 3
    assert db._islands[0][0].metric == 9.0
    assert db._islands[0][-1].metric == 7.0


def test_sample_parent_empty_island_returns_none():
    db = ProgramDatabase(num_islands=2, population_size=5)
    assert db.sample_parent(0) is None


def test_sample_inspirations_excludes_own_island():
    db = ProgramDatabase(num_islands=2, population_size=5)
    db.add("code_a", {"combined_score": 1.0}, generation=0, parent_id=None, island=0)
    db.add("code_b", {"combined_score": 1.0}, generation=0, parent_id=None, island=1)
    inspirations = db.sample_inspirations(0, n=5)
    assert all(p.island != 0 for p in inspirations)


def test_save_and_load_roundtrip(tmp_path):
    db = ProgramDatabase(num_islands=2, population_size=5)
    db.add("code_a", {"combined_score": 1.0}, generation=0, parent_id=None, island=0)
    db.add("code_b", {"combined_score": 2.0}, generation=1, parent_id=None, island=1)
    path = tmp_path / "database.json"
    db.save(path)

    loaded = ProgramDatabase.load(path)
    assert loaded.best_program.code == "code_b"
    assert len(loaded.all_programs()) == 2

    new_program = loaded.add("code_c", {"combined_score": 3.0}, generation=2, parent_id=None, island=0)
    assert new_program.id not in {"prog_000000", "prog_000001"}
