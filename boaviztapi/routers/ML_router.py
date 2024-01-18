import copy
import os

from fastapi import APIRouter, Body, Query

from boaviztapi.dto.ml_setup_dto import MLSetupDTO
from boaviztapi.routers.openapi_doc.descriptions import ml_setup_impact_description
from boaviztapi.routers.openapi_doc.examples import ml_setup_example
from boaviztapi.service.verbose import verbose_setup
from boaviztapi.service.bottom_up import bottom_up_setup

mlca_router = APIRouter(
    prefix='/v1/mlca',
    tags=['mlca']
)


@mlca_router.post('/',
                  description=ml_setup_impact_description)
async def ml_setup_impact_by_config(ml_setup_dto: MLSetupDTO = Body(None, example=ml_setup_example),
                                    verbose: bool = False):
    setup = ml_setup_dto.to_setup()
    # do a deep copy because bottom_up_setup will auto-complete the missing
    # elements ad we need both the incomplete and the completed version for the verbose option
    completed_setup = copy.deepcopy(setup)
    impacts, perspective = bottom_up_setup(setup=completed_setup)
    result = {"impacts": impacts, "perspective": perspective}

    if verbose:
        result = {"impacts": impacts,
                  "perspective": perspective,
                  "verbose": verbose_setup(complete_setup=completed_setup, input_setup=setup)}

    return result
