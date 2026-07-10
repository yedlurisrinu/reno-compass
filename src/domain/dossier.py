"""Dossier domain models and schemas for Reno Compass.

This module defines the strict Pydantic v2 schemas representing the complete
session state contract (dossier.json) along with SemVer checking functions.
"""

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class Dimensions(BaseModel):
    """Spatial dimensions for rooms or elements."""

    length: float = Field(..., description="Length dimension.")
    width: float = Field(..., description="Width dimension.")
    height: float = Field(..., description="Height or thickness dimension.")
    unit: str = Field(..., description="Measurement unit (e.g. 'in', 'ft', 'cm').")


class SubSpace(BaseModel):
    """Sub-spaces built into a room (e.g. closets, bulkheads)."""

    type: str = Field(..., description="Sub-space type vocabulary.")
    dimensions: Dimensions | None = Field(
        default=None, description="Optional dimensions of the sub-space."
    )
    note: str = Field(..., description="Description or function of the sub-space.")


class AreaPreference(BaseModel):
    """Location-specific priority preference."""

    location: str = Field(..., description="Precise spot (e.g. 'shower', 'vanity').")
    preference: str = Field(..., description="Specific want description.")
    priority: Literal["must_have", "nice_to_have"] = Field(
        ..., description="Level of preference priority."
    )


class RoomElement(BaseModel):
    """Visual or physical item inside a room."""

    type: str = Field(..., description="Element type (e.g., 'gfci_outlet', 'exhaust_fan').")
    category: Literal[
        "lighting",
        "plumbing",
        "electrical",
        "hvac",
        "appliance",
        "surface",
        "storage",
        "fixture",
        "other",
    ] = Field(..., description="Best-fit category enum.")
    existing_or_new: Literal["existing", "new"] = Field(
        ..., description="New covers relocations and installs."
    )
    dimensions: Dimensions = Field(
        ..., description="Dimensions are required to force user thought."
    )
    placement: str = Field(..., description="Positional details.")
    brand: str | None = Field(default=None, description="Product brand chosen by user.")
    product_description: str | None = Field(default=None, description="Visual/functional details.")
    spec_note: str | None = Field(default=None, description="Amperage/CFM/load specifications.")


class LightingRequirements(BaseModel):
    """Calculated lighting target outputs for a room."""

    natural_light_note: str = Field(..., description="Exposure and windows summary.")
    light_obstructions: str | None = Field(
        default=None, description="Shades or overhangs blocking light."
    )
    required_natural_lumens: float = Field(..., description="Target natural lumens.")
    recommended_window_area: float = Field(
        ..., description="Suggested window opening size in sqft."
    )
    required_artificial_lumens: float = Field(..., description="IES target output in lumens.")
    required_fixture_count: float = Field(..., description="Minimum fixture count target.")


class IntendedMaterial(BaseModel):
    """Surface material type intent from Design stage."""

    surface: str = Field(..., description="Surface category (e.g., 'floor', 'shower wall').")
    material_type: str = Field(
        ..., description="Material product (e.g., 'porcelain tile', 'quartz')."
    )
    composition: str | None = Field(default=None, description="Natural stone vs quartz vs ceramic.")
    weight_class: str | None = Field(default=None, description="Estimated weight parameters.")
    amperage_note: str | None = Field(default=None, description="Expected amperage load.")


class Room(BaseModel):
    """Room specification and geometry."""

    label: str = Field(..., description="Label identifying the room.")
    dimensions: Dimensions = Field(..., description="Raw spatial dimensions.")
    derived_area: float = Field(..., description="Derived floor area in sqft.")
    derived_volume: float = Field(..., description="Derived room volume.")
    hand_orientation: str | None = Field(default=None, description="Accessibility layout modifier.")
    sub_spaces: list[SubSpace] = Field(
        default_factory=list, description="Subspaces within the room."
    )
    area_preferences: list[AreaPreference] = Field(
        default_factory=list, description="Location-precise preferences."
    )
    elements: list[RoomElement] = Field(
        default_factory=list, description="All elements within the room."
    )
    lighting_requirements: LightingRequirements | None = Field(default=None)
    intended_materials: list[IntendedMaterial] | None = Field(default=None)


class ConversationTurn(BaseModel):
    """A single dialogue turn within a stage conversation."""

    role: Literal["agent", "user"] = Field(..., description="Speaker role.")
    text: str = Field(..., description="Message text.")
    at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Message timestamp."
    )


class SectionStatus(BaseModel):
    """Tracks state and validation gates for each stage."""

    state: Literal["not_started", "in_progress", "completed", "changed_reopened"] = Field(
        default="not_started", description="Orchestration status enum."
    )
    completed_at: datetime | None = Field(default=None, description="When the stage finished.")
    confirmed_at: datetime | None = Field(
        default=None, description="When user provided final verdict."
    )
    confirmation_revoked: bool = Field(default=False, description="True on downstream cascades.")
    depends_on: list[str] = Field(
        default_factory=list, description="Prior stages this stage relies on."
    )


class TierClassificationEnvelope(BaseModel):
    """Envelopes assumed during safety classification."""

    kind: Literal["electrical", "structural", "other"] = Field(
        ..., description="Envelope code category."
    )
    max_amperage: str | None = Field(default=None, description="Limit for existing branch circuit.")
    filled_weight_band: Literal["under_800", "800_1500", "over_1500"] | None = Field(default=None)
    floor_type: Literal["slab", "framed"] | None = Field(default=None)
    aggravating_conditions: list[str] | None = Field(default=None)
    basis: str | None = Field(
        default=None, description="Underlying matrix code threshold citation."
    )


class TierClassification(BaseModel):
    """Per-item safety tier classification details."""

    item: str = Field(..., description="Target renovation item/action.")
    tier: Literal["tier_1_professional", "tier_2_permitted", "tier_3_proceed"] = Field(
        ..., description="Safety tier."
    )
    source: str = Field(..., description="Building code rules source citation.")
    rationale: str = Field(..., description="Logical justification text.")
    depth_consent: bool | None = Field(
        default=None, description="Mandatory for Tier-1 professional review."
    )
    consent_text: str | None = Field(default=None, description="Consent string signature.")
    envelope: TierClassificationEnvelope | None = Field(default=None)
    diy_self_perform_consent: bool = Field(
        default=False,
        description=(
            "Tier-2 only: family explicitly consented to self-perform this item "
            "(distinct from user_permit_consent). Drives DIY-planning eligibility (OM-5/CL-78)."
        ),
    )
    reclassified_from_materials: bool = Field(
        default=False, description="True if breach re-opened Safety."
    )


# Sub-structures for Project Stages
class PropertyContext(BaseModel):
    """Structural and geographic attributes of the property."""

    home_age: int | None = Field(default=None, description="Home construction age.")
    zipcode: str = Field(..., description="ZIP code driving regional cost multipliers.")
    dwelling_type: Literal["independent_house", "condo", "townhouse", "apartment", "other"] = Field(
        ...
    )
    occupancy: Literal["owner_occupied", "rental", "multi_family"] = Field(...)
    occupant_count: int | None = Field(default=None)
    occupant_age_range: dict[str, int | Literal["skipped"] | None] = Field(
        default_factory=lambda: {"youngest": None, "eldest": None}
    )
    has_rental_tenants: bool = Field(default=False)
    renovation_area: float = Field(..., description="Square footage of the target remodel area.")
    dwelling_area: float | None = Field(default=None)
    lot_area: float | None = Field(default=None)


class SpecialConsiderations(BaseModel):
    """Sensitive personal safety and accessibility needs."""

    accessibility_needs: list[str] | Literal["skipped"] | None = Field(default=None)
    health_sensitivities: list[str] | Literal["skipped"] | None = Field(default=None)
    allergies: list[str] | None = Field(default=None, description="Must not rest in skipped state.")
    pets: list[str] | Literal["skipped"] | None = Field(default=None)


class HiddenCondition(BaseModel):
    """Likely unseen hazards surfaced by home age."""

    condition: str
    cost_impact_note: str


class BallparkContingency(BaseModel):
    """Home-age weighted contingency budget."""

    low: float
    high: float
    pct_of_ballpark: float
    capped: bool


class BallparkEstimate(BaseModel):
    """Rough Order of Magnitude ballpark costs."""

    low: float
    high: float
    basis_note: str
    contingency: BallparkContingency


class BudgetRealityCheck(BaseModel):
    """Budget sanity check comparison."""

    stated_vs_ballpark: Literal["plausible", "tight", "unrealistic"]
    note: str


class ScopeStage(BaseModel):
    """Data generated during Stage 1 - Scope."""

    status: SectionStatus = Field(default_factory=SectionStatus)
    conversation: list[ConversationTurn] = Field(default_factory=list)
    project_title: str = Field(..., description="User's project name.")
    project_type: str = Field(..., description="Renovation type.")
    property_context: PropertyContext
    special_considerations: SpecialConsiderations
    global_preferences: list[str] = Field(default_factory=list)
    stated_goal: str = Field(...)
    must_haves: list[str] = Field(default_factory=list)
    nice_to_haves: list[str] = Field(default_factory=list)
    budget_target: float
    budget_ceiling: float
    intended_timing: dict[str, str | None] = Field(
        default_factory=lambda: {"target_window": "", "duration_flexibility": None}
    )
    hidden_conditions: list[HiddenCondition] = Field(default_factory=list)
    ballpark_estimate: BallparkEstimate
    budget_reality_check: BudgetRealityCheck
    budget_reality_resolved: bool = Field(default=False)
    user_final_verdict: bool = Field(default=False)


class RefinedEstimate(BaseModel):
    """Coarse refined cost estimates for design layouts."""

    low: float
    high: float
    includes_professional: bool
    includes_permit: bool
    over_ceiling: bool
    gap_amount: float | None = Field(default=None)


class DesignOption(BaseModel):
    """A proposed design layout layout option."""

    label: str
    option_role: Literal["preferred", "economy", "design_3", "design_4"]
    description: str
    value_proposition: str
    layout: dict[str, list[Room]]
    refined_estimate: RefinedEstimate
    budget_engineered: bool = Field(default=False)
    schematic_ref: str | None = Field(default=None)


class ChosenDesign(BaseModel):
    """The frozen selected design option copied on confirmation."""

    chosen_label: str
    option_role: Literal["preferred", "economy", "design_3", "design_4"]
    layout: dict[str, list[Room]]
    refined_estimate: RefinedEstimate


class DesignStage(BaseModel):
    """Data generated during Stage 2 - Design."""

    status: SectionStatus = Field(default_factory=SectionStatus)
    conversation: list[ConversationTurn] = Field(default_factory=list)
    rooms: list[Room] = Field(default_factory=list)
    options: list[DesignOption] = Field(default_factory=list)
    chosen_design: ChosenDesign | None = Field(default=None)
    user_final_verdict: bool = Field(default=False)
    active_option_role: Literal["preferred", "economy", "design_3", "design_4"] = Field(
        default="preferred"
    )
    retained_analysis: dict[str, dict[str, Any]] = Field(default_factory=dict)


class PermitDisclosure(BaseModel):
    """Permit regulations flagged for local inspection."""

    item: str
    code_reference: str
    ahj_verify_note: str


class EducationalDisclosure(BaseModel):
    """Informational hazard disclosures."""

    topic: str
    trigger: str
    guidance: str
    source: str | None = Field(default=None)


class SafetyPermitStage(BaseModel):
    """Data generated during Stage 3 - Safety & Permit."""

    status: SectionStatus = Field(default_factory=SectionStatus)
    conversation: list[ConversationTurn] = Field(default_factory=list)
    classifications: list[TierClassification] = Field(default_factory=list)
    permit_required: bool = Field(default=False)
    permit_disclosures: list[PermitDisclosure] = Field(default_factory=list)
    educational_disclosures: list[EducationalDisclosure] = Field(default_factory=list)
    user_permit_consent: bool = Field(default=False)
    professional_required: bool = Field(default=False)
    user_final_verdict: bool = Field(default=False)


class DisplacementOption(BaseModel):
    """Displacement cost range alternatives."""

    option: str
    cost_band: dict[str, float] | None = Field(default=None)


class LogisticsFeasibilityStage(BaseModel):
    """Data generated during Stage 4 - Logistics & Feasibility."""

    status: SectionStatus = Field(default_factory=SectionStatus)
    conversation: list[ConversationTurn] = Field(default_factory=list)
    disruption: dict[str, Any] = Field(
        default_factory=lambda: {
            "offline_utilities": [],
            "offline_duration_estimate": "",
            "can_live_through_it": None,
        }
    )
    displacement_options: list[DisplacementOption] = Field(default_factory=list)
    chosen_displacement: str | None = Field(default=None)
    tenant_obligation_note: str | None = Field(default=None)
    weather_timing_note: str | None = Field(default=None)
    total_with_displacement: dict[str, float] = Field(
        default_factory=lambda: {"low": 0.0, "high": 0.0}
    )
    feasible_within_target: bool = Field(default=False)
    feasible_within_ceiling: bool = Field(default=False)
    verdict: Literal[
        "proceed", "use_economy_option", "revisit_design", "proceed_with_budget_gap"
    ] = Field(default="proceed")
    user_final_verdict: bool = Field(default=False)


class MaterialLineItem(BaseModel):
    """An itemized product selected for the renovation."""

    material: str
    category: str
    quantity: float
    unit: str
    room_ref: str
    area: str | None = Field(default=None)
    pricing_mode: Literal["banded", "allowance"]
    waste_factor_pct: float
    cost_band: dict[str, float] | None = Field(default=None)
    unit_cost: float | None = Field(default=None)
    unit_cost_basis: str | None = Field(default=None)
    extended_cost: dict[str, float]
    brand_suggestion: str | None = Field(default=None)
    satisfies_requirement: str | None = Field(default=None)
    allergy_screened: bool = Field(default=False)
    envelope_check: Literal["not_applicable", "within", "breach_reopened_safety"] = Field(
        default="not_applicable"
    )


class MaterialTotal(BaseModel):
    """Rolled up project materials estimates."""

    low: float
    high: float
    allowance_portion: float
    diverges_from_refined: bool


class MaterialsStage(BaseModel):
    """Data generated during Stage 5 - Materials."""

    status: SectionStatus = Field(default_factory=SectionStatus)
    conversation: list[ConversationTurn] = Field(default_factory=list)
    finish_recommendation: dict[str, str] = Field(
        default_factory=lambda: {"palette_note": "", "rationale": ""}
    )
    line_items: list[MaterialLineItem] = Field(default_factory=list)
    spreadsheet_ref: str | None = Field(default=None)
    final_total: MaterialTotal | None = Field(default=None)
    user_final_verdict: bool = Field(default=False)


class CoverageCheckItem(BaseModel):
    """Checklist item audited from contractor quote."""

    required_item: str
    present_in_quote: bool
    note: str


class CornerCuttingFlag(BaseModel):
    """Risk flags detected in quote."""

    flag: str
    severity: Literal["low", "medium", "high"]


class ContractorValidationStage(BaseModel):
    """Data generated during Stage 6 - Contractor Validation."""

    status: SectionStatus = Field(default_factory=SectionStatus)
    conversation: list[ConversationTurn] = Field(default_factory=list)
    quote_provided: bool = Field(default=False)
    quote_source: Literal["text", "pdf"] | None = Field(default=None)
    quote_file_ref: str | None = Field(default=None)
    quote_raw_text: str | None = Field(default=None)
    coverage_check: list[CoverageCheckItem] = Field(default_factory=list)
    corner_cutting_flags: list[CornerCuttingFlag] = Field(default_factory=list)
    advisory_checklist: list[str] = Field(default_factory=list)
    wants_diy: bool | None = Field(
        default=None,
        description=(
            "All-or-none DIY intent captured at the Contractor stage. True = user wants "
            "to self-perform the eligible (non-Tier-1) work, routing to DIY Planning. "
            "False = use contractors for everything, skipping DIY Planning entirely. "
            "None = not yet decided."
        ),
    )
    user_final_verdict: bool = Field(default=False)


class ToolRequired(BaseModel):
    """Tools needed to execute a DIY task."""

    tool: str
    purpose: str
    rent_or_buy_note: str | None = Field(default=None)


class DiyProcedure(BaseModel):
    """Step-by-step instructions for non-Tier-1 work."""

    item: str
    tier: Literal["tier_3_proceed", "tier_2_permitted"]
    steps: list[str] = Field(default_factory=list)
    hold_points: list[str] | None = Field(default=None)
    timeline: dict[str, str] | None = Field(default=None)
    tools: list[ToolRequired] = Field(
        default_factory=list, description="Tools specific to this line item."
    )
    user_feasible: bool | None = Field(
        default=None,
        description=(
            "Per-item DIY decision made in the loop. True = user will self-perform. "
            "False = user opted out; item is reclassified to professional scope. "
            "None = not yet decided (item still pending in the loop)."
        ),
    )
    refine_count: int = Field(
        default=0,
        description="Number of refine/clarify passes spent on this item (capped at 3).",
    )
    reclassify_to_professional: bool = Field(default=False)


class DiyPlanningStage(BaseModel):
    """Data generated during Stage 6.5 - DIY Planning."""

    status: SectionStatus = Field(default_factory=SectionStatus)
    conversation: list[ConversationTurn] = Field(default_factory=list)
    procedures: list[DiyProcedure] = Field(default_factory=list)
    tools_required: list[ToolRequired] = Field(default_factory=list)
    active_item: str | None = Field(
        default=None,
        description="The procedure item currently under discussion in the per-item loop.",
    )
    user_final_verdict: bool = Field(default=False)


class BudgetGapBridge(BaseModel):
    """Financing or scoping bridge alternatives for a budget gap."""

    gap_amount: float
    bridge_options: list[str]


class PhaseChecklists(BaseModel):
    """Project phase check lists."""

    before_demolition: list[str]
    after_demolition: list[str]
    while_reno_in_progress: list[str]
    wrap_up: list[str]


class SynthesisStage(BaseModel):
    """Final output details for Stage 7 - Synthesis."""

    status: SectionStatus = Field(default_factory=SectionStatus)
    design_accepted: bool = Field(default=False)
    has_budget_gap: bool = Field(default=False)
    outcome: Literal["full_plan", "plan_with_budget_gap"] = Field(default="full_plan")
    budget_gap_bridge: BudgetGapBridge | None = Field(default=None)
    phase_checklists: PhaseChecklists | None = Field(default=None)
    diy_scope: list[str] = Field(
        default_factory=list,
        description="Non-Tier-1 items the user confirmed they will self-perform (user_feasible=True).",
    )
    contractor_scope_additions: list[str] = Field(
        default_factory=list,
        description=(
            "Non-Tier-1 items the user opted out of during DIY Planning "
            "(user_feasible=False) — surfaced as 'Add to your contractor's scope'."
        ),
    )
    pdf_ref: str | None = Field(default=None)
    generated_at: datetime | None = Field(default=None)
    user_final_verdict: bool = Field(default=False)


class DossierEnvelope(BaseModel):
    """Dossier root metadata details."""

    app_id: str = Field(default="reno-compass")
    schema_version: str = Field(default="1.1.0")
    dossier_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    origin: Literal["fresh", "session_restore"] = Field(default="fresh")
    current_stage: Literal[
        "scope",
        "design",
        "safety_permit",
        "logistics_feasibility",
        "materials",
        "contractor_validation",
        "diy_planning",
        "synthesis",
        "complete",
    ] = Field(default="scope")


class ProjectBody(BaseModel):
    """Holder for individual stage outputs."""

    scope: ScopeStage | None = Field(default=None)
    design: DesignStage | None = Field(default=None)
    safety_permit: SafetyPermitStage | None = Field(default=None)
    logistics_feasibility: LogisticsFeasibilityStage | None = Field(default=None)
    materials: MaterialsStage | None = Field(default=None)
    contractor_validation: ContractorValidationStage | None = Field(default=None)
    diy_planning: DiyPlanningStage | None = Field(default=None)
    synthesis: SynthesisStage | None = Field(default=None)


class Dossier(BaseModel):
    """Root model for the entire session state JSON document."""

    envelope: DossierEnvelope
    project: ProjectBody


# Versioning & Schema Migration Helpers (SemVer checking)
def parse_semver(version_str: str) -> list[int]:
    """Parses a semantic version string into a list of integers.

    Args:
        version_str: Semantic version string e.g. "1.2.3"

    Returns:
        List of [major, minor, patch] integers.
    """
    parts = version_str.strip().split(".")
    if len(parts) != 3:
        raise ValueError(f"Invalid SemVer string format: {version_str}")
    return [int(p) for p in parts]


def check_schema_version(dossier_version: str, current_version: str = "1.1.0") -> tuple[bool, str]:
    """Verifies semantic version compatibility between imported file and target app.

    Enforces Dimension 11 (SemVer check):
    * Major version mismatch -> Hard block/start-fresh reject.
    * Minor version mismatch -> Warn and allow best-effort load.
    * Patch version mismatch -> Load silently.

    Args:
        dossier_version: The version string loaded from the dossier.
        current_version: The active schema version of the application.

    Returns:
        A tuple of (is_compatible: bool, status_message: str).
    """
    try:
        d_major, d_minor, d_patch = parse_semver(dossier_version)
        c_major, c_minor, c_patch = parse_semver(current_version)
    except ValueError:
        return False, "Failed to parse semantic version structure."

    if d_major != c_major:
        return (
            False,
            f"Major schema mismatch ({dossier_version} vs {current_version}). Reload rejected.",
        )

    if d_minor > c_minor:
        return (
            True,
            f"Import version is newer ({dossier_version}). Proceeding with best-effort conversion.",
        )

    if d_minor < c_minor:
        return (
            True,
            f"Import version is older ({dossier_version}). Upgrading to current schema version.",
        )

    return True, "Schema version matches exactly."
