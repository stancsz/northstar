# LiteLLM dependency inventory

This inventory supports the active goal to revise current route terminology to
LiteLLM at port 4000. It distinguishes Northstar's configurable client
dependencies from historical Subroute-era wording. It does not change the route
or establish live service behavior.

## Active configurable dependencies

- **Codex CLI workers:** The current [local routing guide](litellm-routing.md)
  specifies `http://127.0.0.1:4000/v1`, model alias `default`, and the
  `GATEWAY_MASTER_KEY` process environment variable. It identifies the exact
  Codex profile as `subroute-subagents` and says to explicitly override its
  base URL. The profile's actual local definition is not in this repository;
  this is a profile identifier, not evidence of the profile's current contents.
- **Advisor Council:** This is a separately configured client, not an
  unconditional dependency on the worker profile or endpoint. The
  [installation guide](install.md) and [Advisor skill](../../skills/advisor-council/SKILL.md)
  specify `EXPERTS_BASE_URL` and `EXPERTS_API_KEY` (or explicit CLI options).
  The [routing guide](litellm-routing.md) says the Advisor can be pointed at
  `http://127.0.0.1:4000/v1` when deliberately configured with matching
  credentials. Therefore the Advisor endpoint is independently configured;
  do not imply it always uses port 4000. The Windows user-key fallback and
  loopback restriction are described by the skill.
- **Optional Advisor-directed reader:** The [reader reference](../../skills/advisor-council/references/reader.md)
  and [Pi reader source](../../skills/advisor-council/scripts/pi_reader.mjs)
  use `READER_BASE_URL` or inherit `EXPERTS_BASE_URL`, plus their separately
  named key settings. This optional path can be configured independently too.

## Exact identifiers and endpoint facts

| Purpose | Exact repository-documented value | Qualification |
| --- | --- | --- |
| Codex profile | `subroute-subagents` | Identifier in the current route guide; profile definition is external to this repository. |
| Worker/API base URL | `http://127.0.0.1:4000/v1` | Current owner-selected local LiteLLM route in the guide. |
| Worker model alias | `default` | Configured alias, not a claim about resolved upstream model identity. |
| Worker credential variable | `GATEWAY_MASTER_KEY` | Process environment variable name only; no value is recorded here. |
| Advisor base URL setting | `EXPERTS_BASE_URL` or `--base-url` | Separately configured client setting. |
| Advisor key setting | `EXPERTS_API_KEY` | Separate credential variable; no value is recorded here. |
| Reader base URL settings | `READER_BASE_URL` or `EXPERTS_BASE_URL` | Optional reader configuration; see its reference for key behavior. |

## Historical references retained as history

Historical documents use **Subroute** as a product, repository, gateway, or
deployment name. Those references remain evidence of what was inspected or
tested at the time; they are not current route configuration and should not be
rewritten as if they established today's service state. Examples:

- [Local inference routing evaluation](../evals/local-inference-routing.md)
  and [Claude route evaluation](../evals/rea-skill-stack/claude-route.md)
  retain dated route and preflight evidence.
- [Central package evaluation](../evals/central-package.md) and
  [Advisor image evaluation](../evals/advisor-images.md) record historical
  Subroute source, container, alias, and LiteLLM test observations.
- [Dispatch-context implementation report](../reports/dispatch-context/implementation.md)
  and [Subroute tool-preflight report](../reports/dispatch-context/subroute-tool-preflight-guard-20261023.md)
  retain historical profile, route, and failure details.
- [Delivery-focus goal](../goal/delivery-focus/GOAL.md) preserves prior
  route-selection, gateway, and Advisor-boundary observations with their
  limitations.

The repository also contains many dated evaluation receipts and reports with
the historical name. Their existence alone does not make Subroute a distinct
current client dependency. Generated runtime data and local run artifacts are
outside this inventory's evidence set.

## Unknown runtime behavior

This source/document inventory does not inspect the local profile definition,
process environment, running listeners, container configuration, current
LiteLLM deployment, or resolved alias mapping. It therefore cannot establish
that port 4000 is listening, that the exact profile currently points there,
that `default` resolves to a particular provider/model, or that any request
will succeed. Nor does a historical successful request establish current
availability. The independently configured Advisor endpoint may be different
from the worker endpoint unless deliberately aligned by configuration.

## Scope and verification

The inventory was assembled from targeted `rg` searches of current guidance
and source plus `git grep` over tracked historical documentation, excluding
generated runtime data and run artifacts. Links above are relative to this
file. No configuration, profile, runtime state, historical evidence, or other
durable file was changed by the inventory worker; no live service was probed
as part of its inventory checks.
