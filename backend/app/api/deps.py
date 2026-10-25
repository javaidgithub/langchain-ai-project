from fastapi import Request

from app.services.threads import ThreadRepository


def get_graphs(request: Request) -> dict:
    return request.app.state.graphs


def get_threads(request: Request) -> ThreadRepository:
    return request.app.state.threads
