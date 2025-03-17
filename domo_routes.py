import domolibrary.client.get_data as gd
import domolibrary.client.DomoAuth as dmda
import domolibrary.client.DomoError as dmde


async def get_workflow(
    auth: dmda.DomoAuth, model_id, version_id, debug_api: bool = False
):

    url = f"https://{auth.domo_instance}.domo.com/api/workflow/v1/models/{model_id}/versions/{version_id}"
    res = await gd.get_data(auth=auth, method="GET", url=url, debug_api=debug_api)

    if not res.is_success:
        raise dmde.RouteError(res=res)

    return res


def generate_trigger_workflow_body(
    starting_tile, model_id, version_id, execution_params: dict
):
    return {
        "messageName": starting_tile,
        "version": version_id,
        "modelId": model_id,
        "data": execution_params,
    }


async def trigger_workflow(
    auth: dmda.DomoAuth,
    starting_tile: str,
    model_id: str,
    version_id: str,
    execution_parameters: dict = None,
    debug_api: bool = False,
):
    body = generate_trigger_workflow_body(
        starting_tile=starting_tile,
        model_id=model_id,
        execution_params=execution_parameters,
        version_id=version_id,
    )

    url = f"https://{auth.domo_instance}.domo.com/api/workflow/v1/instances/message"

    res = await gd.get_data(
        method="POST", url=url, body=body, auth=auth, debug_api=debug_api
    )

    if not res.is_success:
        raise dmde.RouteError(res=res)

    return res
