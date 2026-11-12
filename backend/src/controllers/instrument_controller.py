from ..services import instrument_service
from ..models.instrument import InstrumentPair
from ..models.common import serialize
from .common import listing,require
def list_all(db):return listing(db,InstrumentPair)
def detail(db,ident):return serialize(require(db,InstrumentPair,ident))
def create(db,body):return serialize(instrument_service.create(db,body))
