from ..services import study_service
from ..models.study import CalibrationStudy
from ..models.common import serialize
from .common import listing,require
def list_all(db):return listing(db,CalibrationStudy)
def detail(db,ident):return serialize(require(db,CalibrationStudy,ident))
def create(db,body):return serialize(study_service.create(db,body))
