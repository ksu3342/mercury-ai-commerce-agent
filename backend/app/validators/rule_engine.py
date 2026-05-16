from __future__ import annotations

import re
from typing import Dict, Iterable, List, Optional

from app.schemas import (
    ComplianceIssue,
    ComplianceReport,
    GeneratedListing,
    MarketConfig,
    PolicyRule,
    ProductInput,
)


class RuleEngine:
    """Deterministic checks for the demo workflow."""

    def __init__(
        self,
        policy_rules: Iterable[PolicyRule],
        market_configs: Iterable[MarketConfig],
    ) -> None:
        self.policy_rules: Dict[str, PolicyRule] = {rule.rule_id: rule for rule in policy_rules}
        self.market_configs: Dict[str, MarketConfig] = {
            config.market_id: config for config in market_configs
        }

    def check(self, product: ProductInput, listings: Iterable[GeneratedListing]) -> List[ComplianceReport]:
        return [self._check_listing(product, listing) for listing in listings]

    def _check_listing(self, product: ProductInput, listing: GeneratedListing) -> ComplianceReport:
        market = self.market_configs[listing.market_id]
        checks: List[ComplianceIssue] = []

        checks.extend(self._check_required_fields(product, listing, market))
        checks.append(self._check_title_length(listing, market))
        checks.extend(self._check_forbidden_terms(listing, market))
        checks.extend(self._check_brand_term_preserved(product, listing))
        checks.extend(self._check_battery_fields(product, listing))
        checks.extend(self._check_electrical_power_fields(product, listing))
        checks.extend(self._check_compatibility_claim_scope(product, listing))
        checks.extend(self._check_safety_claims(product, listing))
        checks.extend(self._check_food_contact(product, listing))
        checks.extend(self._check_unit_consistency(product, listing))
        checks.extend(self._check_rule_references(listing))

        failed_count = sum(1 for item in checks if item.status == "failed")
        warning_count = sum(1 for item in checks if item.status == "warning")
        blocker_count = sum(
            1 for item in checks if item.status == "failed" and item.severity == "blocker"
        )
        overall_status = "blocker" if blocker_count else "warning" if warning_count else "pass"
        score = max(0, 100 - blocker_count * 20 - warning_count * 8 - failed_count * 5)
        policy_version = market.compliance_profile.get("policy_version", "unknown")

        return ComplianceReport(
            report_id=f"rpt_{self._normalize_id(product.sku)}_{listing.market_id.lower()}",
            run_id=listing.run_id,
            trace_id=listing.trace_id,
            listing_id=listing.listing_id,
            market_id=listing.market_id,
            overall_status=overall_status,
            score=score,
            checks=checks,
            validator_result={
                "json_schema_passed": True,
                "deterministic_validators_passed": blocker_count == 0,
                "failed_validator_count": failed_count,
                "warning_count": warning_count,
                "blocker_count": blocker_count,
            },
            retrieved_chunks=listing.retrieved_chunks,
            policy_version=policy_version,
        )

    def _check_required_fields(
        self,
        product: ProductInput,
        listing: GeneratedListing,
        market: MarketConfig,
    ) -> List[ComplianceIssue]:
        checks: List[ComplianceIssue] = []
        for field in market.required_attributes:
            if self._value_exists(listing.attributes.get(field)):
                continue

            rule_id = self._rule_for_required_field(field, market)
            rule = self.policy_rules.get(rule_id)
            checks.append(
                ComplianceIssue(
                    issue_id=f"chk_{listing.market_id.lower()}_required_{field}",
                    rule_id=rule_id,
                    status="failed",
                    severity=rule.severity if rule else "warning",
                    message=(rule.message if rule else f"Missing required field: {field}"),
                    evidence={"field": f"attributes.{field}", "value": listing.attributes.get(field)},
                    suggestion=(rule.remediation if rule else f"Provide {field}."),
                )
            )
        return checks

    def _check_title_length(self, listing: GeneratedListing, market: MarketConfig) -> ComplianceIssue:
        max_length = int(market.locale_rules.get("max_title_length", 150))
        length = len(listing.title)
        if length <= max_length:
            return ComplianceIssue(
                issue_id=f"chk_{listing.market_id.lower()}_title_length",
                rule_id="TITLE_LENGTH_BY_MARKET",
                status="passed",
                severity="warning",
                message="Title length is within the configured market limit.",
                evidence={"length": length, "max_length": max_length},
                suggestion=None,
            )
        return ComplianceIssue(
            issue_id=f"chk_{listing.market_id.lower()}_title_length",
            rule_id="TITLE_LENGTH_BY_MARKET",
            status="warning",
            severity="warning",
            message="Title exceeds the configured market limit.",
            evidence={"length": length, "max_length": max_length},
            suggestion="Shorten the title before mock export.",
        )

    def _check_forbidden_terms(
        self,
        listing: GeneratedListing,
        market: MarketConfig,
    ) -> List[ComplianceIssue]:
        risky_terms = {self._claim_term(term) for term in market.forbidden_claims}
        risky_terms.update(term.replace("_", " ") for term in market.forbidden_claims)
        risky_terms.discard("")
        if listing.market_id == "US":
            risky_terms.update({"cure", "treat", "guaranteed healthy", "100% safe"})

        if not risky_terms:
            return []

        risky_terms.update(term.replace("_", " ") for term in market.forbidden_claims)
        text = self._listing_text(listing).lower().replace("%", " percent")
        matched = sorted(term for term in risky_terms if term in text)

        if listing.market_id != "US" and not matched:
            return []

        status = "failed" if matched else "passed"
        rule_id = (
            "US_UNSUPPORTED_HEALTH_CLAIM"
            if listing.market_id == "US"
            else "MARKET_FORBIDDEN_CLAIM"
        )
        return [
            ComplianceIssue(
                issue_id=f"chk_{listing.market_id.lower()}_forbidden_claim",
                rule_id=rule_id,
                status=status,
                severity="blocker",
                message=(
                    "Forbidden or unsupported claim was found."
                    if matched
                    else "No forbidden or unsupported claim was found."
                ),
                evidence={"matched_terms": matched},
                suggestion="Remove medical, treatment, safety guarantee, or weight-loss language."
                if matched
                else None,
            )
        ]

    def _check_brand_term_preserved(
        self,
        product: ProductInput,
        listing: GeneratedListing,
    ) -> List[ComplianceIssue]:
        if not product.brand:
            return []
        if product.brand in listing.title:
            return []
        return [
            ComplianceIssue(
                issue_id=f"chk_{listing.market_id.lower()}_brand_term",
                rule_id="BRAND_TERM_DO_NOT_TRANSLATE",
                status="warning",
                severity="warning",
                message="Brand term is missing from the listing title.",
                evidence={"brand": product.brand, "title": listing.title},
                suggestion=f"Keep brand term {product.brand} exactly as provided.",
            )
        ]

    def _check_battery_fields(
        self,
        product: ProductInput,
        listing: GeneratedListing,
    ) -> List[ComplianceIssue]:
        if "battery" not in product.regulatory_tags:
            return []

        missing = [
            field
            for field in ("battery_capacity_mah", "charger_type")
            if not self._value_exists(listing.attributes.get(field))
        ]
        return [
            ComplianceIssue(
                issue_id=f"chk_{listing.market_id.lower()}_battery_fields",
                rule_id="BATTERY_CAPACITY_FIELD_REQUIRED",
                status="passed" if not missing else "failed",
                severity="warning",
                message=(
                    "Battery capacity and charger type are preserved in structured attributes."
                    if not missing
                    else "Rechargeable battery fields are missing from structured attributes."
                ),
                evidence={
                    "battery_capacity_mah": listing.attributes.get("battery_capacity_mah"),
                    "charger_type": listing.attributes.get("charger_type"),
                    "missing_fields": missing,
                },
                suggestion="Keep battery_capacity_mah and charger_type in export payload.",
            )
        ]

    def _check_food_contact(
        self,
        product: ProductInput,
        listing: GeneratedListing,
    ) -> List[ComplianceIssue]:
        if "food_contact" not in product.regulatory_tags:
            return []

        text = self._listing_text(listing).lower()
        absolute_terms = ["100% safe", "medically safe", "guaranteed safe"]
        matched = [term for term in absolute_terms if term in text]
        if matched:
            status = "failed"
            evidence = {"matched_terms": matched}
            suggestion = "Remove absolute safety guarantees and keep material facts only."
        elif listing.market_id == "DE":
            status = "warning"
            evidence = {"claim": self._first_claim_text(listing)}
            suggestion = "Keep material facts and avoid broad safety wording."
        else:
            status = "passed"
            evidence = {"matched_terms": []}
            suggestion = None

        return [
            ComplianceIssue(
                issue_id=f"chk_{listing.market_id.lower()}_food_contact_tone",
                rule_id="FOOD_CONTACT_MATERIAL_DISCLOSURE",
                status=status,
                severity="warning",
                message="Food contact material language should stay factual.",
                evidence=evidence,
                suggestion=suggestion,
            )
        ]

    def _check_electrical_power_fields(
        self,
        product: ProductInput,
        listing: GeneratedListing,
    ) -> List[ComplianceIssue]:
        if not self._is_electrical_product(product):
            return []

        required_fields = ["power_watt"]
        if product.category_hint == "consumer_electronics":
            required_fields.extend(["input_voltage", "output_voltage"])
        missing = [
            field for field in required_fields if not self._value_exists(listing.attributes.get(field))
        ]
        rule = self.policy_rules.get("ELECTRICAL_POWER_FIELD_REQUIRED")
        return [
            ComplianceIssue(
                issue_id=f"chk_{listing.market_id.lower()}_electrical_power",
                rule_id="ELECTRICAL_POWER_FIELD_REQUIRED",
                status="passed" if not missing else "failed",
                severity=rule.severity if rule else "blocker",
                message=(
                    "Electrical power fields are preserved in structured attributes."
                    if not missing
                    else "Electrical power fields are missing from structured attributes."
                ),
                evidence={
                    "power_watt": listing.attributes.get("power_watt"),
                    "input_voltage": listing.attributes.get("input_voltage"),
                    "output_voltage": listing.attributes.get("output_voltage"),
                    "missing_fields": missing,
                },
                suggestion=(rule.remediation if rule else "Add verified electrical rating fields."),
            )
        ]

    def _check_compatibility_claim_scope(
        self,
        product: ProductInput,
        listing: GeneratedListing,
    ) -> List[ComplianceIssue]:
        if "compatibility_claim" not in product.regulatory_tags:
            return []

        terms = ["works with all devices", "compatible with every device", "universal for all"]
        text = self._listing_text(listing).lower()
        matched = sorted(term for term in terms if term in text)
        if not matched:
            return []
        rule = self.policy_rules.get("COMPATIBILITY_CLAIM_NEEDS_SCOPE")
        return [
            ComplianceIssue(
                issue_id=f"chk_{listing.market_id.lower()}_compatibility_scope",
                rule_id="COMPATIBILITY_CLAIM_NEEDS_SCOPE",
                status="warning",
                severity=rule.severity if rule else "warning",
                message="Broad compatibility claim needs a supported scope.",
                evidence={"matched_terms": matched},
                suggestion=(rule.remediation if rule else "Scope compatibility claim to supported devices."),
            )
        ]

    def _check_safety_claims(
        self,
        product: ProductInput,
        listing: GeneratedListing,
    ) -> List[ComplianceIssue]:
        if not self._is_electrical_product(product) and "safety_claim" not in product.regulatory_tags:
            return []

        terms = ["100 percent safe", "100% safe", "guaranteed safe", "risk-free"]
        text = self._listing_text(listing).lower().replace("%", " percent")
        matched = sorted(term for term in terms if term in text)
        if not matched:
            return []
        rule = self.policy_rules.get("SAFETY_CLAIM_NEEDS_EVIDENCE")
        return [
            ComplianceIssue(
                issue_id=f"chk_{listing.market_id.lower()}_safety_claim",
                rule_id="SAFETY_CLAIM_NEEDS_EVIDENCE",
                status="failed",
                severity=rule.severity if rule else "blocker",
                message="Absolute safety claim needs evidence before approval.",
                evidence={"matched_terms": matched},
                suggestion=(rule.remediation if rule else "Remove unsupported safety wording."),
            )
        ]

    def _check_unit_consistency(
        self,
        product: ProductInput,
        listing: GeneratedListing,
    ) -> List[ComplianceIssue]:
        expected_capacity = product.attributes.get("capacity_ml")
        if not expected_capacity:
            return []

        text = self._listing_text(listing)
        capacities = {int(match) for match in re.findall(r"(\d+)\s*ml", text, flags=re.I)}
        mismatched = sorted(value for value in capacities if value != int(expected_capacity))
        if not mismatched:
            return []

        return [
            ComplianceIssue(
                issue_id=f"chk_{listing.market_id.lower()}_unit_consistency",
                rule_id="UNIT_CONSISTENCY_BASIC",
                status="warning",
                severity="warning",
                message="Capacity values in text do not match product attributes.",
                evidence={"expected_capacity_ml": expected_capacity, "found_capacity_ml": mismatched},
                suggestion="Use the capacity value from ProductInput.attributes.capacity_ml.",
            )
        ]

    def _check_rule_references(self, listing: GeneratedListing) -> List[ComplianceIssue]:
        checks: List[ComplianceIssue] = []
        for ref in listing.retrieved_chunks:
            if ref.rule_id and ref.rule_id not in self.policy_rules:
                checks.append(
                    ComplianceIssue(
                        issue_id=f"chk_unknown_rule_{ref.chunk_id}",
                        rule_id=ref.rule_id,
                        status="warning",
                        severity="warning",
                        message="Retrieved chunk references a rule_id not present in policy_rules.jsonl.",
                        evidence={"chunk_id": ref.chunk_id, "rule_id": ref.rule_id},
                        suggestion="Update policy_rules.jsonl or remove the stale retrieved chunk.",
                    )
                )
        return checks

    def _rule_for_required_field(self, field: str, market: MarketConfig) -> str:
        if field == "responsible_person" and market.region == "EU":
            return "EU_GPSR_RESPONSIBLE_PERSON_REQUIRED"
        if field in {"battery_capacity_mah", "charger_type"}:
            return "BATTERY_CAPACITY_FIELD_REQUIRED"
        if field in {"power_watt", "input_voltage", "output_voltage"}:
            return "ELECTRICAL_POWER_FIELD_REQUIRED"
        return "REQUIRED_FIELD_PRESENT"

    def _listing_text(self, listing: GeneratedListing) -> str:
        claim_text = " ".join(claim.text for claim in listing.claims)
        bullets = " ".join(listing.bullet_points)
        return f"{listing.title} {bullets} {listing.description} {claim_text}"

    def _first_claim_text(self, listing: GeneratedListing) -> Optional[str]:
        return listing.claims[0].text if listing.claims else None

    def _value_exists(self, value: object) -> bool:
        if value is None:
            return False
        if isinstance(value, str) and not value.strip():
            return False
        return True

    def _claim_term(self, term: str) -> str:
        return term.lower().replace("_", " ").replace("%", " percent").strip()

    def _normalize_id(self, value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")

    def _is_electrical_product(self, product: ProductInput) -> bool:
        return (
            product.category_hint in {"home_lighting", "consumer_electronics"}
            or "electrical_safety" in product.regulatory_tags
            or "power_rating" in product.regulatory_tags
        )
