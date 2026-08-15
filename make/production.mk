ARGS = $(filter-out $@,$(MAKECMDGOALS))
ARG  = $(firstword $(ARGS))

export MK_ARG   = $(ARGS)
export MK_SECS  = $(SECS)
export MK_CMD   = $(CMD)
export MK_SINCE = $(SINCE)

CHECK_ARG   = case "$$MK_ARG" in *[!a-z0-9_-]*) echo "invalid $(UNIT): $$MK_ARG" >&2; exit 1;; esac
CHECK_SECS  = [ -z "$$MK_SECS" ] || case "$$MK_SECS" in *[!0-9]*) echo "SECS must be digits" >&2; exit 1;; esac
CHECK_SINCE = [ -z "$$MK_SINCE" ] || case "$$MK_SINCE" in *[!0-9smh]*) echo "SINCE must be like 5m, 2h, 90s" >&2; exit 1;; esac
CHECK_CMD   = case "$$MK_CMD" in *"'"*) echo "CMD must not contain a single quote" >&2; exit 1;; esac

SSH     := ssh root@duckalpha
SSH_TTY := ssh -tt root@duckalpha

SH_BIN         ?= bash
STREAM_TIMEOUT ?= 3600
EVENT_SINCE    ?= 5m

ONE_ARG = [ "$(words $(ARGS))" = 1 ] || { echo "Usage: make $@ <$(UNIT)>"; exit 1; }
STREAM  = exec timeout --foreground -s INT $(or $(SECS),$(STREAM_TIMEOUT))

RESOLVE_IN  = names=$$(docker ps $(2) --filter "name=$(call NAME_RE,$(1))" --format "{{.Names}}"); \
              n=$$(printf "%s" "$$names" | grep -c "."); \
              [ "$$n" = 1 ] || { echo "expected 1 container matching $(call NAME_RE,$(1)); found $$n" >&2; \
                                 [ "$$n" = 0 ] || printf "%s\n" "$$names" >&2; exit 1; }; \
              name=$$names
RESOLVE     = $(call RESOLVE_IN,$(1),)
RESOLVE_ANY = $(call RESOLVE_IN,$(1),-a)

.PHONY: help lint check hooks ps images logs deployed inspect stats volumes networks events sh exec
lint:  ## Fast quality checks: make lint
	uv run pre-commit run lint --all-files

check:  ## Types, unused code, dependency hygiene: make check
	uv run pre-commit run check --all-files

hooks:  ## Install pre-commit git hooks: make hooks
	uv run pre-commit install

help:  ## This help
	@grep -hE '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

ps:  ## Container status: make ps
	@$(SSH) 'docker ps --format "table {{.Names}}\t{{.Status}}" | awk "NR==1 || /$(PS_RE)/"'

images:  ## Image tag each container runs: make images
	@$(SSH) 'docker ps --format "{{.Names}} {{.Image}}" | grep -E "$(PS_RE)" | sort'

logs:  ## Tail logs: make logs <unit> [SECS=60]
	@$(ONE_ARG)
	@$(CHECK_ARG)
	@$(CHECK_SECS)
	@$(SSH_TTY) '$(call RESOLVE,$(ARG)); $(STREAM) docker logs --tail=200 -f "$$name"' || [ $$? = 124 ]

deployed:  ## When a container last started: make deployed <unit>
	@$(ONE_ARG)
	@$(CHECK_ARG)
	@$(SSH) '$(call RESOLVE_ANY,$(ARG)); docker inspect -f "{{.Name}} {{.State.Status}} started {{.State.StartedAt}}" "$$name"'

inspect:  ## Container JSON without env: make inspect <unit>
	@$(ONE_ARG)
	@$(CHECK_ARG)
	@$(SSH) '$(call RESOLVE_ANY,$(ARG)); docker inspect "$$name"' | jq 'del(.[].Config.Env)'

stats:  ## CPU, memory and disk, one shot: make stats
	@$(SSH) 'docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" $$(docker ps --filter "name=$(PS_RE)" -q); echo; docker system df'

volumes:  ## Docker volumes: make volumes [name-filter]
	@$(CHECK_ARG)
	@$(SSH) 'docker volume ls $(if $(ARGS),--filter "name=$(ARG)",)'

networks:  ## Docker networks: make networks [name-filter]
	@$(CHECK_ARG)
	@$(SSH) 'docker network ls $(if $(ARGS),--filter "name=$(ARG)",)'

events:  ## Container events in a window: make events [SINCE=5m]
	@$(CHECK_SINCE)
	@$(SSH) 'docker events --filter type=container --since $(or $(SINCE),$(EVENT_SINCE)) --until 0s --format "{{.Time}} {{.Action}} {{.Actor.Attributes.name}}"'

sh:  ## Interactive shell: make sh <unit> | make sh
	@$(CHECK_ARG)
	@$(if $(ARGS),$(SSH_TTY) '$(call RESOLVE,$(ARG)); exec timeout --foreground $(STREAM_TIMEOUT) docker exec -it "$$name" $(SH_BIN)',$(SSH_TTY))

exec:  ## One-shot command: make exec <unit> CMD="<cmd>" [TTY=1]
	@$(CHECK_CMD)
	@[ "$(words $(ARGS))" = 1 ] && [ -n "$$MK_CMD" ] || { echo 'Usage: make exec <$(UNIT)> CMD="<cmd>" [TTY=1]'; exit 1; }
	@$(CHECK_ARG)
	@$(if $(TTY),$(SSH_TTY),$(SSH)) '$(call RESOLVE,$(ARG)); exec timeout --foreground $(STREAM_TIMEOUT) docker exec $(if $(TTY),-it )"$$name" $(CMD)'

%:
	@:
