from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.reply_corpus import ReplyCorpus
from app.schemas.reply_corpus import ReplyCorpusUpsertRequest
from app.services.reply_corpus_service import (
    build_reply_corpus_context,
    delete_reply_corpus,
    get_reply_corpus_dashboard,
    save_reply_corpus,
)


def _make_session():
    temp_dir = tempfile.TemporaryDirectory()
    db_path = Path(temp_dir.name) / "reply_corpus.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return temp_dir, engine, SessionLocal()


class ReplyCorpusServiceTests(unittest.TestCase):
    def test_reply_corpus_context_and_crud(self):
        temp_dir, engine, db = _make_session()
        self.addCleanup(temp_dir.cleanup)
        self.addCleanup(engine.dispose)
        self.addCleanup(db.close)

        first = save_reply_corpus(
            db,
            ReplyCorpusUpsertRequest(
                title="高情商回复",
                target_person_type="colleague",
                scene_type="follow_up",
                content="先接住情绪，再给一个短而稳的回应。",
                sort_order=10,
                is_enabled=True,
            ),
        )
        second = save_reply_corpus(
            db,
            ReplyCorpusUpsertRequest(
                title="职场婉拒",
                target_person_type="boss",
                scene_type="formal_notice",
                content="先给结论，再补一句边界，不要过度解释。",
                sort_order=1,
                is_enabled=False,
            ),
        )

        dashboard = get_reply_corpus_dashboard(db)
        self.assertEqual(len(dashboard["items"]), 2)
        self.assertEqual(first.title, "高情商回复")
        self.assertEqual(first.target_person_type, "colleague")
        self.assertEqual(first.scene_type, "follow_up")
        self.assertIn("同事", first.corpus_type)
        self.assertEqual(second.target_person_type, "boss")
        self.assertEqual(second.scene_type, "formal_notice")
        self.assertIn("上司", second.corpus_type)

        context = build_reply_corpus_context(db)
        self.assertIn("高情商回复", context)
        self.assertIn("先接住情绪", context)
        self.assertNotIn("职场婉拒", context)

        deleted = delete_reply_corpus(db, first.id)
        self.assertEqual(deleted.id, first.id)
        remaining = db.query(ReplyCorpus).all()
        self.assertEqual(len(remaining), 1)

    def test_reply_corpus_context_filters_by_scope(self):
        temp_dir, engine, db = _make_session()
        self.addCleanup(temp_dir.cleanup)
        self.addCleanup(engine.dispose)
        self.addCleanup(db.close)

        save_reply_corpus(
            db,
            ReplyCorpusUpsertRequest(
                title="通用高情商",
                target_person_type="any",
                scene_type="any",
                content="先接住情绪，再给结论。",
                sort_order=10,
                is_enabled=True,
            ),
        )
        save_reply_corpus(
            db,
            ReplyCorpusUpsertRequest(
                title="职场跟进",
                target_person_type="colleague",
                scene_type="follow_up",
                content="先说结论，再补下一步。",
                sort_order=20,
                is_enabled=True,
            ),
        )
        save_reply_corpus(
            db,
            ReplyCorpusUpsertRequest(
                title="暧昧推进",
                target_person_type="crush",
                scene_type="push_forward",
                content="先接住，再轻轻往前走一步。",
                sort_order=30,
                is_enabled=True,
            ),
        )

        scope_context = build_reply_corpus_context(db, target_person_type="crush", scene_type="push_forward")
        self.assertIn("暧昧推进", scope_context)
        self.assertIn("先接住，再轻轻往前走一步", scope_context)
        self.assertIn("通用高情商", scope_context)
        self.assertNotIn("职场跟进", scope_context)


if __name__ == "__main__":
    unittest.main()
