import sqlalchemy as sa
import sqlalchemy.orm as orm
from app import db, create_app
from app.models import User, Task, Notification, Message, Document, Analysis, DocChunk

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {
        "sa": sa,
        "orm": orm,
        "db": db,
        "Document": Document,
        "Analysis": Analysis,
        "DocChunk": DocChunk,
    }
