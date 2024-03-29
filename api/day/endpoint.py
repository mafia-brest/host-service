from bottle import request, response
from psycopg2.errors import ForeignKeyViolation, UniqueViolation
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from api.app import app
from api.db import Session
from model import DayModel
from .validation import GameDayResponse, GameDayCreateRequest, GameDayPatchRequest


def get_last_day_number_of_game(session, game_id):
    last_day = session.query(DayModel)\
        .where(DayModel.game_id == game_id)\
        .order_by(DayModel.number.desc())\
        .limit(1)\
        .one_or_none()

    return last_day and last_day.number or 1


@app.post('/day')
def create_game_day():
    try:
        game_data = GameDayCreateRequest(**request.json)
    except ValidationError as e:
        response.status = 400
        return {'error': str(e)}

    with Session() as session:
        new_day = DayModel(**game_data.dict())
        new_day.number = new_day.number or get_last_day_number_of_game(session, new_day.game_id) + 1
        session.add(new_day)

        try:
            session.commit()
        except IntegrityError as error:
            if isinstance(error.orig, ForeignKeyViolation):
                response.status = 404
                return {'error': 'The game not found'}
            if isinstance(error.orig, UniqueViolation):
                response.status = 409
                return {
                    'error': 'The day with specified number '
                             'already exists in the game'
                }

        response.content_type = 'application/json'
        return GameDayResponse.from_orm(new_day).json()


@app.route('/day/<id>', 'PATCH')
def update_game_day(id: int):
    try:
        day_data = GameDayPatchRequest(**request.json)
    except ValidationError as e:
        return {'error': str(e)}

    with Session() as session:
        is_day_present = session.query(DayModel).where(
            DayModel.id == id).update(day_data.dict())
        if not is_day_present:
            response.status = 404
            return {'error': 'Day not found'}

        session.commit()


@app.delete('/day/<id>')
def delete_game_day(id: int):
    with Session() as session:
        day = session.query(DayModel).where(DayModel.id == id).one_or_none()
        if day is None:
            response.status = 404
            return {'error': 'Day not found'}

        session.delete(day)
        session.commit()
