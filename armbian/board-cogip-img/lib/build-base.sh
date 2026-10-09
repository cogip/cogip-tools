#!/bin/bash
# Build or refresh the per-TARGET BASE image: the heavy, class-generic part
# (packages + the cogip.cpp wheel built under qemu + service enablement). Built
# once per TARGET and reused; the per-robot instance data is added afterwards by
# provision.sh. Rebuilt only when the app source hash changes, or BASE_REBUILD=1.
#
# Relies on vars set by build.sh: SCRIPT_DIR TARGET BOARD BRANCH RELEASE
# ARMBIAN_BUILD_DIR UP IMAGES_DIR REPO_ROOT. Sets: BASE_IMG.

# Hash of everything baked into the BASE image: the app source (wheel/venv) AND
# the build recipe (customize-image.sh + the board/target fragments -> config.txt
# and services, the common + target overlays). A change in any of these
# invalidates the base; a different ROBOT_ID alone does not (that is provision-only).
cogip_source_hash() {
    {
        # App inputs: git-tracked files only (ls-files excludes submodule
        # contents, gitignored files and untracked artifacts like __pycache__),
        # so stray local build junk under cogip/ does not churn the base.
        git -C "${REPO_ROOT}" ls-files -z -co --exclude-standard -- \
                cogip pyproject.toml uv.lock .python-version CMakeLists.txt 2>/dev/null \
            | while IFS= read -r -d '' f; do sha256sum "${REPO_ROOT}/${f}"; done
        # Build recipe: our own files, explicitly scoped (no repo-root junk).
        sha256sum "${SCRIPT_DIR}/userpatches/customize-image.sh" \
                  "${SCRIPT_DIR}/customize.d/board-${BOARD}.sh" \
                  "${SCRIPT_DIR}/customize.d/target-${TARGET}.sh" 2>/dev/null
        find "${SCRIPT_DIR}/userpatches/overlay" -type f -exec sha256sum {} + 2>/dev/null | sort
        [ -d "${SCRIPT_DIR}/overlay-${TARGET}" ] && \
            find "${SCRIPT_DIR}/overlay-${TARGET}" -type f -exec sha256sum {} + 2>/dev/null | sort
        # Armbian identity: release/branch/ref + the checked-out build-framework
        # commit, so a different Armbian version (or a `git pull` in it) also
        # invalidates the base. BOARD is already in the base image name.
        printf 'armbian %s %s %s\n' "${RELEASE}" "${BRANCH}" "${ARMBIAN_REF:-}"
        git -C "${ARMBIAN_BUILD_DIR}" rev-parse HEAD 2>/dev/null || true
    } | sha256sum | cut -d' ' -f1
}

# Generated minimal Armbian config with the board fragment appended, so Armbian
# registers its config.txt hook (lib.config is no longer supported). The
# fragment's variable assignments are harmless in this context.
_cogip_write_config() {
    local conf="${UP}/config-$1.conf"
    cat > "${conf}" <<EOF
BOARD="${BOARD}"
COGIP_TARGET="${TARGET}"
BRANCH="${BRANCH}"
RELEASE="${RELEASE}"
KERNEL_CONFIGURE="no"
BUILD_DESKTOP="no"
BUILD_MINIMAL="yes"
KERNEL_GIT="shallow"
COMPRESS_OUTPUTIMAGE="sha,img"
EOF
    [ -f "${SCRIPT_DIR}/customize.d/board-${BOARD}.sh" ] \
        && cat "${SCRIPT_DIR}/customize.d/board-${BOARD}.sh" >> "${conf}"
}

# Stage ONLY class-generic files into the build overlay: the common overlay, the
# target overlay, the cogip project (wheel build input) and base.conf (TARGET).
# No per-robot instance files here (those are provisioned later).
_cogip_stage_base_overlay() {
    rm -rf "${UP}/overlay"; mkdir -p "${UP}/overlay"
    cp "${SCRIPT_DIR}/userpatches/customize-image.sh" "${UP}/customize-image.sh"
    chmod +x "${UP}/customize-image.sh"
    cp -r "${SCRIPT_DIR}/userpatches/overlay/." "${UP}/overlay/"
    if [ -d "${SCRIPT_DIR}/overlay-${TARGET}" ]; then
        cp -r "${SCRIPT_DIR}/overlay-${TARGET}/." "${UP}/overlay/"
        echo "Target overlay staged: overlay-${TARGET}."
    fi
    mkdir -p "${UP}/overlay/etc/cogip"
    printf 'COGIP_TARGET=%s\n' "${TARGET}" > "${UP}/overlay/etc/cogip/base.conf"

    # Stage the board + target fragments where customize-image.sh sources them
    # (${FRAG}=/usr/local/lib/cogip-build); customize removes them at the end so
    # they do not ship in the image.
    local frag="${UP}/overlay/usr/local/lib/cogip-build"; mkdir -p "${frag}"
    [ -f "${SCRIPT_DIR}/customize.d/board-${BOARD}.sh" ] \
        && cp "${SCRIPT_DIR}/customize.d/board-${BOARD}.sh" "${frag}/"
    cp "${SCRIPT_DIR}/customize.d/target-${TARGET}.sh" "${frag}/"

    local dest="${UP}/overlay/opt"; mkdir -p "${dest}"
    local p
    for p in pyproject.toml uv.lock .python-version CMakeLists.txt LICENSE; do
        [ -e "${REPO_ROOT}/${p}" ] && cp "${REPO_ROOT}/${p}" "${dest}/"
    done
    # Stage only git-tracked files under cogip/ (rsync creates parent dirs), so
    # no host build junk (__pycache__, stray .so) leaks into the in-image wheel
    # build. Matches what cogip_source_hash counts.
    rm -rf "${dest}/cogip"
    git -C "${REPO_ROOT}" ls-files -z -co --exclude-standard -- cogip \
        | rsync -a --from0 --files-from=- "${REPO_ROOT}/" "${dest}/"
    echo "COGIP project staged into /opt."
}

cogip_ensure_base() {
    BASE_IMG="${IMAGES_DIR}/base-${TARGET}-${BOARD}.img"
    local hashfile="${IMAGES_DIR}/base-${TARGET}-${BOARD}.hash"
    local want; want=$(cogip_source_hash)

    if [ -f "${BASE_IMG}" ] && [ "$(cat "${hashfile}" 2>/dev/null)" = "${want}" ] && [ -z "${BASE_REBUILD:-}" ]; then
        echo "Base up to date: ${BASE_IMG##*/} (source ${want:0:12})."
        return 0
    fi

    echo "Building base TARGET=${TARGET} BOARD=${BOARD} (source ${want:0:12})..."
    _cogip_stage_base_overlay
    local cfg="base-${TARGET}-${BOARD}"
    _cogip_write_config "${cfg}"
    ( cd "${ARMBIAN_BUILD_DIR}" && ./compile.sh "${cfg}" )

    local out; out=$(ls -t "${IMAGES_DIR}"/*.img 2>/dev/null | head -1 || true)
    [ -n "${out}" ] || { echo "Armbian produced no image" >&2; return 1; }
    if [ "${out}" != "${BASE_IMG}" ]; then
        rm -f "${BASE_IMG}" "${BASE_IMG}".*
        mv "${out}" "${BASE_IMG}"
        rm -f "${out}.sha" "${out}.bmap"
    fi
    mkdir -p "${IMAGES_DIR}"; printf '%s\n' "${want}" > "${hashfile}"
    echo "Base built: ${BASE_IMG##*/}."
}
