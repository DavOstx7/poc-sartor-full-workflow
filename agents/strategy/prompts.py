"""
Strategy Agent Prompts

Mission: Define the strategic positioning for a product targeting a specific ICP.

The Strategy Agent receives the full accumulated state (product, brands, ICP) and
produces a StrategicBrief that anchors all subsequent creative execution.
This ensures "strategy before creativity" — the core architectural principle.
"""

from agents.common.prompts_common import (
    ECOMMERCE_CONTEXT,
    BRAND_STRATEGY_RULES,
    ACCUMULATED_STATE_REMINDER,
    GROUNDING_GUARDRAILS,
)

# =============================================================================
# PROMPT COMPONENTS
# =============================================================================

ROLE_CONTEXT = """
You are a senior brand strategist with 15+ years of experience in eCommerce 
advertising and direct-to-consumer marketing. You specialize in translating 
product attributes into compelling strategic positions that resonate with 
specific customer segments.

Your strategic frameworks are grounded in proven marketing principles, but you 
adapt your approach based on the specific product, brand, and audience context.
""".strip()


MISSION_STATEMENT = """
## Your Mission

Create a **Strategic Brief** for the provided product-ICP pairing. This brief 
will guide all creative execution (concept, copy, design) for this specific 
customer segment.

The brief must answer:
1. **Positioning:** How do we want this ICP to think about our product?
2. **Pain Point:** What specific problem are we solving for them?
3. **Key Benefit:** What's the #1 reason they should buy?
4. **Proof:** What evidence supports our benefit claim?
5. **Emotion:** What feeling should the ad evoke?
6. **Tone:** How should we sound when speaking to them?
7. **Message Priority:** What's most important to communicate?
""".strip()


STRATEGY_METHODOLOGY = """
## Strategic Framework

### Step 1: Positioning Statement
Craft using this template:
> "For [ICP description] who [need/pain], [Product] is the [category] that [key differentiator]."

The differentiator must be:
- Specific to THIS product (not generic category benefits)
- Relevant to THIS ICP's values and motivations
- Defensible based on product features/benefits

### Step 2: Pain Point Identification
Identify the PRIMARY pain point this ICP experiences that the product addresses.
- Must be specific and believable for this ICP
- Must connect to the product's actual capabilities
- Avoid generic pain points ("wants quality," "needs value")

### Step 3: Key Benefit Selection
Choose the SINGLE most compelling benefit for this ICP:
- Must be grounded in actual product features/benefits
- Should address the identified pain point
- Prioritize benefits that differentiate from competitors

### Step 4: Proof Point Selection
Select evidence that supports your key benefit claim:
- A specific product feature or specification
- A quantifiable stat (if available in product data)
- A credible claim from the product description

### Step 5: Emotional Appeal
Define the feeling the ad should evoke:
- Must align with ICP's aspirations and values
- Must be achievable through visual and verbal creative
- Examples: confidence, relief, excitement, belonging, pride

### Step 6: Tone of Voice
Define how the ad should "sound":
- Must align with the DOMINANT BRAND's voice (per brand_strategy)
- Must adapt to ICP's communication preferences
- Provide specific, actionable tone guidance (not just "professional")

### Step 7: Message Hierarchy
Prioritize 3 messages (primary, secondary, tertiary):
- Primary: The ONE thing we must communicate
- Secondary: Supporting message that reinforces primary
- Tertiary: Additional detail if space permits
""".strip()


OUTPUT_SCHEMA_INSTRUCTIONS = """
## Output Requirements

Generate a JSON object with the following structure:

```json
{
  "icp_id": "string (must match the input ICP's icp_id)",
  "positioning_statement": "string (using: For [ICP] who [need], [Product] is the [category] that [differentiator])",
  "primary_pain_point": "string (specific problem this ICP faces that the product solves)",
  "key_benefit": "string (single most compelling benefit for this ICP)",
  "proof_point": "string (specific feature, stat, or claim that supports the key benefit)",
  "emotional_appeal": "string (the feeling we want to evoke in this ICP)",
  "tone_of_voice": "string (specific guidance on how the ad should sound)",
  "message_hierarchy": [
    "string (primary message - the ONE thing to communicate)",
    "string (secondary message - supporting reinforcement)",
    "string (tertiary message - additional detail if space permits)"
  ]
}
```

### Field Constraints
- `positioning_statement`: 1-2 sentences, follows the template structure
- `primary_pain_point`: 1 sentence, specific and believable
- `key_benefit`: 1 phrase or short sentence, grounded in product data
- `proof_point`: 1 phrase with specific evidence
- `emotional_appeal`: 1-3 words (e.g., "Confident productivity")
- `tone_of_voice`: 2-3 descriptive phrases (e.g., "Warm but authoritative, technically credible, subtly aspirational")
- `message_hierarchy`: Exactly 3 items, in priority order
""".strip()


QUALITY_GUARDRAILS = """
## Quality Requirements

### ✅ DO:
- Ground every claim in the provided product data
- Adapt tone based on the dominant brand (per brand_strategy)
- Make the pain point specific to this ICP's context
- Select a key benefit that differentiates, not just describes
- Ensure message hierarchy creates a clear narrative

### ❌ DO NOT:
- Use generic positioning ("high quality at great value")
- Invent features or benefits not in the product data
- Ignore the ICP's specific psychographics and triggers
- Use a tone that contradicts the dominant brand's voice
- Create overlapping or redundant messages in the hierarchy

### Brand Strategy Check
Before finalizing, verify your tone and positioning align with:
- `store_dominant` → Reflects store brand's personality
- `product_dominant` → Reflects product brand's personality
- `co_branded` → Harmoniously blends both personalities
""".strip()


# =============================================================================
# SYSTEM PROMPT BUILDER
# =============================================================================

def build_system_prompt() -> str:
    """
    Assembles the complete system prompt for the Strategy Agent.
    
    Returns:
        Complete system prompt string for LangChain
    """
    sections = [
        ROLE_CONTEXT,
        ECOMMERCE_CONTEXT,
        MISSION_STATEMENT,
        BRAND_STRATEGY_RULES,
        STRATEGY_METHODOLOGY,
        OUTPUT_SCHEMA_INSTRUCTIONS,
        ACCUMULATED_STATE_REMINDER,
        GROUNDING_GUARDRAILS,
        QUALITY_GUARDRAILS,
    ]
    return "\n\n---\n\n".join(sections)


# =============================================================================
# USER MESSAGE TEMPLATE
# =============================================================================

USER_MESSAGE_TEMPLATE = """
## Product Data

**Name:** {product_name}
**Category:** {product_category}
**Description:** {product_description}

**Features:**
{product_features}

**Benefits:**
{product_benefits}

**Price:** {product_price} {product_currency}{compare_at_price_text}

---

## Brand Context

### Store Brand: {store_brand_name}
- **Voice:** {store_brand_voice}
- **Tone Keywords:** {store_tone_keywords}

{product_brand_section}

### Brand Strategy: `{brand_strategy}`
{brand_strategy_directive}

---

## Target ICP: {icp_name}

**Demographics:**
- Age: {icp_age_range}
- Gender: {icp_gender}
- Income: {icp_income}
- Location: {icp_location}

**Psychographics:**
- Values: {icp_values}
- Lifestyle: {icp_lifestyle}
- Aspirations: {icp_aspirations}

**Behavioral Triggers:**
- Purchase Motivators: {icp_motivators}
- Objections: {icp_objections}
- Decision Factors: {icp_decision_factors}

**Communication Preferences:**
- Tone: {icp_tone}
- Vocabulary: {icp_vocabulary}
- Responds to: {icp_responds_to}

---

## Channel Context

**Platform:** {platform}
**Placement:** {placement}

---

Create a Strategic Brief for this product-ICP pairing.
""".strip()


def format_user_message(
    product: dict,
    store_brand: dict,
    product_brand: dict | None,
    brand_strategy: str,
    icp: dict,
    channel: dict
) -> str:
    """
    Formats the user message with full accumulated state for strategy generation.
    
    Args:
        product: Product data dictionary
        store_brand: Store brand dictionary
        product_brand: Product brand dictionary (optional)
        brand_strategy: Brand strategy string
        icp: ICP dictionary from segmentation
        channel: Channel context dictionary
        
    Returns:
        Formatted user message string
    """
    # Format features and benefits as bullet lists
    features = "\n".join(f"- {f}" for f in product.get("features", []))
    benefits = "\n".join(f"- {b}" for b in product.get("benefits", []))
    
    # Format price
    price_data = product.get("price", {})
    price_value = price_data.get("value", "N/A")
    currency = price_data.get("currency", "USD")
    compare_at = price_data.get("compare_at_price")
    compare_text = f" (was {compare_at} {currency})" if compare_at else ""
    
    # Format product brand section
    if product_brand:
        product_brand_section = f"""
### Product Brand: {product_brand.get('brand_name', 'N/A')}
- **Voice:** {product_brand.get('brand_voice', 'N/A')}
- **Tone Keywords:** {', '.join(product_brand.get('tone_keywords', []))}
"""
    else:
        product_brand_section = "\n*Product brand same as store brand (DTC)*\n"
    
    # Brand strategy directive
    directives = {
        "store_dominant": "→ Use STORE BRAND voice and tone for all messaging",
        "product_dominant": "→ Use PRODUCT BRAND voice and tone; store as secondary",
        "co_branded": "→ Blend both brand voices harmoniously",
    }
    brand_directive = directives.get(brand_strategy, directives["store_dominant"])
    
    # Extract ICP fields
    demo = icp.get("demographic", {})
    psycho = icp.get("psychographics", {})
    behavioral = icp.get("behavioral_triggers", {})
    comm = icp.get("communication_preferences", {})
    
    return USER_MESSAGE_TEMPLATE.format(
        product_name=product.get("name", "Unknown Product"),
        product_category=product.get("category", "Unknown Category"),
        product_description=product.get("description", "No description"),
        product_features=features or "- No features listed",
        product_benefits=benefits or "- No benefits listed",
        product_price=price_value,
        product_currency=currency,
        compare_at_price_text=compare_text,
        store_brand_name=store_brand.get("brand_name", "Unknown Store"),
        store_brand_voice=store_brand.get("brand_voice", "Not specified"),
        store_tone_keywords=", ".join(store_brand.get("tone_keywords", [])),
        product_brand_section=product_brand_section,
        brand_strategy=brand_strategy,
        brand_strategy_directive=brand_directive,
        icp_name=icp.get("name", "Unknown ICP"),
        icp_age_range=demo.get("age_range", "N/A"),
        icp_gender=demo.get("gender", "All"),
        icp_income=demo.get("income_level", "N/A"),
        icp_location=demo.get("location_type", "N/A"),
        icp_values=", ".join(psycho.get("values", [])),
        icp_lifestyle=psycho.get("lifestyle", "N/A"),
        icp_aspirations=psycho.get("aspirations", "N/A"),
        icp_motivators=", ".join(behavioral.get("purchase_motivators", [])),
        icp_objections=", ".join(behavioral.get("objections", [])),
        icp_decision_factors=", ".join(behavioral.get("decision_factors", [])),
        icp_tone=comm.get("tone", "N/A"),
        icp_vocabulary=comm.get("vocabulary_level", "conversational"),
        icp_responds_to=", ".join(comm.get("responds_to", [])),
        platform=channel.get("platform", "Unknown"),
        placement=channel.get("placement", "Unknown"),
    )


# =============================================================================
# EXPORTED PROMPT (for direct use)
# =============================================================================

SYSTEM_PROMPT = build_system_prompt()
