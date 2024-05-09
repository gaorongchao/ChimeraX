from typing import Optional, Union, Annotated

from chimerax.core.commands import (
    CmdDesc,
    ModelIdArg,
    EnumOf,
    register,
    run,
    Or,
    BoolArg,
    IntArg,
    Int2Arg,
    Int3Arg,
)
from chimerax.core.errors import UserError
from chimerax.ui.cmd import ui_tool_show
from chimerax.map import Volume

from chimerax.segmentations.dicom_segmentations import (
    PlanePuckSegmentation,
    SphericalSegmentation,
)

from chimerax.segmentations.segmentation import Segmentation, segment_volume
from chimerax.segmentations.ui.segmentation_mouse_mode import (
    save_mouse_bindings,
    restore_mouse_bindings,
    save_hand_bindings,
    restore_hand_bindings,
)
from chimerax.segmentations.settings import get_settings
from chimerax.segmentations.types import Axis

actions = [
    "add",
    "remove",
    "create",
    "setMouseModes",
    "resetMouseModes",
    "setHandModes",
    "resetHandModes",
]


def segmentations(
    session,
    action,
    modelSpecifier=None,
    axis: Optional[str] = None,
    # Axial, Coronal, Sagittal slice segmentations
    planeCenter: Optional[
        Union[
            tuple[int, int],
            Annotated[list[int], 2],
        ]
    ] = None,
    # Spherical segmentations
    sphereCenter: Optional[
        Union[
            tuple[int, int, int],
            Annotated[list[int], 3],
        ]
    ] = None,
    slice: Optional[int] = None,
    radius: Optional[int] = None,
    minIntensity: Optional[int] = None,
    maxIntensity: Optional[int] = None,
    openTool: Optional[bool] = False,
):
    """Set or restore hand modes; or add, delete, or modify segmentations."""
    settings = get_settings(session)
    if session.ui.is_gui:
        if openTool:
            tool = get_segmentation_tool(session)
    if action == "create":
        if not modelSpecifier:
            raise UserError("No model specified")
        reference_model = [
            model for model in session.models if model.id == modelSpecifier
        ][0]
        if not isinstance(reference_model, Volume):
            raise UserError(
                "Must specify a volume to segment; try narrowing your model specifier (e.g. #1 --> #1.1)"
            )
        new_seg = segment_volume(reference_model, 1)
        new_seg.set_parameters(surface_levels=[0.501])
        new_seg.set_step(1)
        new_seg.set_transparency(
            int((settings.default_segmentation_opacity / 100) * 255)
        )
        session.models.add([new_seg])
    elif action == "add":
        if not modelSpecifier:
            raise UserError("No segmentation specified")
        model = [model for model in session.models if model.id == modelSpecifier][0]
        if isinstance(model, Segmentation):
            if planeCenter:
                axis = Axis.from_string(axis)
                if not slice:
                    raise UserError("Must specify a slice for a 2d segmentation")
                segment_in_circle(
                    model,
                    axis,
                    slice,
                    planeCenter,
                    radius,
                    minIntensity,
                    maxIntensity,
                    1,
                )
            elif sphereCenter:
                if axis:
                    session.logger.info(
                        "Ignoring the Axis parameter for a 3D segmentation"
                    )
                model_center = model.world_coordinates_for_data_point(sphereCenter)
                segment_in_sphere(
                    model, model_center, radius, minIntensity, maxIntensity, 1
                )
        else:
            raise UserError("Can't add to a non-segmentation")
    elif action == "remove":
        if not modelSpecifier:
            raise UserError("No segmentation specified")
        model = [model for model in session.models if model.id == modelSpecifier][0]
        if isinstance(model, Segmentation):
            if planeCenter:
                axis = Axis.from_string(axis)
                if not slice:
                    raise UserError("Must specify a slice for a 2d segmentation")
                if minIntensity or maxIntensity:
                    session.logger.info(
                        "Ignoring the intensity parameters for removing regions from a segmentation"
                    )
                segment_in_circle(
                    model,
                    axis,
                    slice,
                    planeCenter,
                    radius,
                    minIntensity,
                    maxIntensity,
                    0,
                )
            elif sphereCenter:
                if axis:
                    session.logger.info(
                        "Ignoring the Axis parameter for a 3D segmentation"
                    )
                model_center = model.world_coordinates_for_data_point(sphereCenter)
                segment_in_sphere(
                    model, model_center, radius, minIntensity, maxIntensity, 0
                )
        else:
            raise UserError("Can't add to a non-segmentation")
    elif action == "setMouseModes":
        save_mouse_bindings(session)
        run(session, "ui mousemode shift wheel 'resize segmentation cursor'")
        run(session, "ui mousemode right 'create segmentations'")
        run(session, "ui mousemode shift right 'erase segmentations'")
        run(session, "ui mousemode shift middle 'move segmentation cursor'")
    elif action == "resetMouseModes":
        restore_mouse_bindings(session)
    elif action == "setHandModes":
        save_hand_bindings(session, settings.vr_handedness)
        if settings.vr_handedness == "right":
            offhand = "left"
        else:
            offhand = "right"
        run(
            session,
            f"vr button b 'erase segmentations' hand { str(settings.vr_handedness).lower() }",
        )
        run(
            session,
            f"vr button a 'create segmentations' hand { str(settings.vr_handedness).lower() }",
        )
        run(session, f"vr button x 'toggle segmentation visibility' hand { offhand }")
        run(
            session,
            f"vr button thumbstick 'resize segmentation cursor' hand { str(settings.vr_handedness).lower() }",
        )
        run(
            session,
            f"vr button grip 'move segmentation cursor' hand { str(settings.vr_handedness).lower() }",
        )
    elif action == "resetHandModes":
        restore_hand_bindings(session)


def segment_in_sphere(
    model: Segmentation,
    origin: Union[tuple[int, int, int], Annotated[list[int], 3]],
    radius: int,
    minimum_intensity: int,
    maximum_intensity: int,
    value: int = 1,
) -> None:
    segmentation_strategy = SphericalSegmentation(origin, radius, value)
    if value != 0:
        segmentation_strategy.min_threshold = minimum_intensity
        segmentation_strategy.max_threshold = maximum_intensity
    model.segment(segmentation_strategy)


def segment_in_circle(
    model: Segmentation,
    axis,
    slice,
    center,
    radius,
    min_intensity,
    max_intensity,
    value=1,
):
    center_x, center_y = center
    positions = [(center_x, center_y, radius)]
    segmentation_strategy = PlanePuckSegmentation(axis, slice, positions, value)
    if value != 0:
        segmentation_strategy.min_threshold = min_intensity
        segmentation_strategy.max_threshold = max_intensity
    model.segment(segmentation_strategy)


def open_segmentation_tool(session):
    ui_tool_show(session, "segmentations")


def get_segmentation_tool(session):
    from chimerax.segmentations.ui import find_segmentation_tool

    open_segmentation_tool(session)
    tool = find_segmentation_tool(session)
    return tool


segmentations_desc = CmdDesc(
    required=[("action", EnumOf(actions))],
    optional=[
        ("modelSpecifier", ModelIdArg),
        ("axis", EnumOf([str(axis) for axis in [*Axis]])),
        # TODO: File a bug about how this can't just be ("center", Or(Int2Arg, Int3Arg))
        ("planeCenter", Int2Arg),
        ("sphereCenter", Int3Arg),
        ("slice", IntArg),
        ("radius", IntArg),
        ("minIntensity", IntArg),
        ("maxIntensity", IntArg),
        ("openTool", BoolArg),
    ],
    synopsis="Set the view window to a grid of orthoplanes or back to the default",
)


def register_seg_cmds(logger):
    register(
        "segmentations",
        segmentations_desc,
        segmentations,
        logger=logger,
    )
