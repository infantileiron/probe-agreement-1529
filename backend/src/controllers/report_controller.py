from ..services import report_service
from ..models.report import Report
from ..models.common import serialize
from .common import listing,require
def list_all(db):return listing(db,Report)
def detail(db,ident):return serialize(require(db,Report,ident))
def create(db,body):return serialize(report_service.create(db,body))
