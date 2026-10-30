python

# -*- coding: utf-8 -*-

"""
file_manager.py

Python 2.7
Linux / Windows
External modules: None

Functions:
    copy(src, dst)
    move(src, dst)
    remove(path)
    makedir(path)

Return:
    True  : Success
    False : Failed (including partial failure)
"""

import os
import glob
import shutil
import stat


# ============================================================
# User settings
# ============================================================

# 삭제 금지 경로
#
# 보호 경로 자체와 그 상위 경로는 삭제할 수 없음.
# 보호 경로 내부의 하위 파일 및 폴더는 삭제 가능.
#
# Examples:
#   '/home/user/important'
#   '/etc'
#   'C:/Windows'

PROTECTED_PATHS = [
    # '/home/user/important',
    # '/etc',
    # 'C:/Windows',
]


# ============================================================
# Internal utilities
# ============================================================

def _normalize(path):
    """Normalize Linux / Windows path separators."""

    if not path:
        return ''

    path = path.replace('\\', os.sep)
    path = path.replace('/', os.sep)

    return os.path.normpath(os.path.abspath(path))


def _is_link(path):
    return os.path.islink(path)


def _exists(path):
    return os.path.lexists(path)


def _has_wildcard(path):
    return '*' in path or '?' in path


def _is_inside(path, parent):
    """Check whether path is parent or a descendant of parent."""

    path = os.path.normcase(_normalize(path))
    parent = os.path.normcase(_normalize(parent))

    if path == parent:
        return True

    return path.startswith(parent.rstrip(os.sep) + os.sep)


def _is_root(path):
    """Check filesystem root or Windows drive root."""

    path = _normalize(path)

    drive, tail = os.path.splitdrive(path)

    if not tail or tail == os.sep:
        return True

    if path == os.sep:
        return True

    return False


def _is_safe_delete(path):
    """Check whether a path can be deleted."""

    if not path:
        return False

    # Reject paths containing parent traversal.
    raw = path.replace('\\', '/')

    if '..' in raw.split('/'):
        return False

    target = _normalize(path)

    if not target:
        return False

    # Never delete filesystem roots.
    if _is_root(target):
        return False

    # Reject current working directory itself.
    if os.path.normcase(target) == os.path.normcase(
            _normalize(os.curdir)):
        return False

    # Check configured protected paths.
    for protected in PROTECTED_PATHS:

        if not protected:
            continue

        protected_paths = glob.glob(
            _normalize(protected)
        ) if _has_wildcard(protected) else [
            _normalize(protected)
        ]

        for protected_path in protected_paths:

            # Cannot delete the protected path itself
            # or any parent containing it.
            if _is_inside(protected_path, target):
                return False

    return True


def _ensure_parent(path):
    """Create parent directories when necessary."""

    parent = os.path.dirname(path)

    if parent and not os.path.isdir(parent):
        os.makedirs(parent)


def _remove_readonly(path):
    """Try to remove read-only attribute."""

    try:
        os.chmod(path, stat.S_IWRITE)
    except Exception:
        pass


def _delete_raw(path):
    """
    Internal deletion.
    Does not check PROTECTED_PATHS.
    Used only for replacing destinations and moving.
    """

    if not _exists(path):
        return True

    try:

        if _is_link(path):
            os.remove(path)
            return True

        if os.path.isdir(path):

            success = True

            try:
                names = os.listdir(path)
            except Exception:
                return False

            for name in names:

                child = os.path.join(path, name)

                if not _delete_raw(child):
                    success = False

            try:
                _remove_readonly(path)
                os.rmdir(path)
            except Exception:
                success = False

            return success

        _remove_readonly(path)
        os.remove(path)

        return True

    except Exception:
        return False


def _copy_file(src, dst):

    try:
        _ensure_parent(dst)

        if _exists(dst) and not os.path.isdir(dst):
            _remove_readonly(dst)

        shutil.copy2(src, dst)

        return True

    except Exception:
        return False


def _copy_symlink(src, dst):

    try:
        _ensure_parent(dst)

        if _exists(dst):
            if not _delete_raw(dst):
                return False

        target = os.readlink(src)
        os.symlink(target, dst)

        return True

    except Exception:
        return False


def _copy_dir(src, dst):
    """Recursive directory copy with merge."""

    try:

        if _is_inside(dst, src):
            return False

        if _exists(dst):

            if _is_link(dst) or not os.path.isdir(dst):

                if not _delete_raw(dst):
                    return False

                os.makedirs(dst)

        else:
            os.makedirs(dst)

        success = True

        for name in os.listdir(src):

            source = os.path.join(src, name)
            target = os.path.join(dst, name)

            if not _copy_one(source, target):
                success = False

        try:
            shutil.copystat(src, dst)
        except Exception:
            pass

        return success

    except Exception:
        return False


def _copy_one(src, dst):

    try:

        if _is_link(src):
            return _copy_symlink(src, dst)

        if os.path.isdir(src):
            return _copy_dir(src, dst)

        if os.path.isdir(dst):
            dst = os.path.join(dst, os.path.basename(src))

        return _copy_file(src, dst)

    except Exception:
        return False


def _move_one(src, dst):

    try:

        if _is_link(src):
            if os.path.isdir(dst):
                dst = os.path.join(dst, os.path.basename(src))

            _ensure_parent(dst)

            if _exists(dst):
                if not _delete_raw(dst):
                    return False

            shutil.move(src, dst)
            return True

        if os.path.isdir(src):

            if _is_inside(dst, src):
                return False

            if os.path.isdir(dst) and not _is_link(dst):

                # Merge into existing directory.
                success = True

                for name in os.listdir(src):

                    source = os.path.join(src, name)
                    target = os.path.join(dst, name)

                    if not _move_one(source, target):
                        success = False

                try:
                    os.rmdir(src)
                except Exception:
                    success = False

                return success

            _ensure_parent(dst)

            if _exists(dst):
                if not _delete_raw(dst):
                    return False

            shutil.move(src, dst)
            return True

        # Source is a file.
        if os.path.isdir(dst):
            dst = os.path.join(dst, os.path.basename(src))

        _ensure_parent(dst)

        if _exists(dst):
            if not _delete_raw(dst):
                return False

        shutil.move(src, dst)

        return True

    except Exception:
        return False


def _wildcard_base(pattern):
    """Find base directory before first wildcard."""

    pattern = _normalize(pattern)

    index = len(pattern)

    for char in ('*', '?'):

        pos = pattern.find(char)

        if pos >= 0:
            index = min(index, pos)

    prefix = pattern[:index]

    if prefix.endswith(os.sep):
        base = prefix.rstrip(os.sep)
    else:
        base = os.path.dirname(prefix)

    if not base:
        base = os.curdir

    return _normalize(base)


def _wildcard_sources(pattern):
    """Return matching paths and their common base."""

    matches = glob.glob(pattern)

    if not matches:
        return [], None

    base = _wildcard_base(pattern)

    result = []

    for item in matches:

        item = _normalize(item)

        try:
            relative = os.path.relpath(item, base)
        except Exception:
            return [], None

        if relative == os.pardir or relative.startswith(
                os.pardir + os.sep):
            return [], None

        result.append((item, relative))

    return result, base


# ============================================================
# Public functions
# ============================================================

def makedir(path):
    """Create directory including all missing parents."""

    try:

        if not path or _has_wildcard(path):
            return False

        path = _normalize(path)

        if os.path.isdir(path):
            return True

        if _exists(path):
            return False

        os.makedirs(path)

        return True

    except Exception:
        return False


def copy(src, dst):
    """Copy files/directories. Existing files are overwritten."""

    try:

        if not src or not dst:
            return False

        wildcard = _has_wildcard(src)

        if wildcard:

            sources, base = _wildcard_sources(src)

            # No matches is not an error.
            if not sources:
                return True

            dst = _normalize(dst)

            if _exists(dst) and not os.path.isdir(dst):
                return False

            if not os.path.isdir(dst):
                os.makedirs(dst)

            success = True

            for source, relative in sources:

                target = os.path.join(dst, relative)

                if not _copy_one(source, target):
                    success = False

            return success

        src = _normalize(src)
        dst_raw = dst
        dst = _normalize(dst)

        if not _exists(src):
            return False

        if os.path.isdir(src) and not _is_link(src):

            # Trailing separator means destination container.
            if dst_raw.endswith(('/', '\\')):
                dst = os.path.join(dst, os.path.basename(src))

            if _is_inside(dst, src):
                return False

            return _copy_dir(src, dst)

        if os.path.isdir(dst):
            dst = os.path.join(dst, os.path.basename(src))

        return _copy_one(src, dst)

    except Exception:
        return False


def move(src, dst):
    """Move files/directories. Existing destinations are replaced or merged."""

    try:

        if not src or not dst:
            return False

        wildcard = _has_wildcard(src)

        if wildcard:

            sources, base = _wildcard_sources(src)

            if not sources:
                return True

            dst = _normalize(dst)

            if _exists(dst) and not os.path.isdir(dst):
                return False

            if not os.path.isdir(dst):
                os.makedirs(dst)

            success = True

            for source, relative in sources:

                target = os.path.join(dst, relative)

                if not _move_one(source, target):
                    success = False

            return success

        src = _normalize(src)
        dst_raw = dst
        dst = _normalize(dst)

        if not _exists(src):
            return False

        if os.path.isdir(src) and not _is_link(src):

            if dst_raw.endswith(('/', '\\')):
                dst = os.path.join(dst, os.path.basename(src))

            if _is_inside(dst, src):
                return False

            return _move_one(src, dst)

        if os.path.isdir(dst):
            dst = os.path.join(dst, os.path.basename(src))

        return _move_one(src, dst)

    except Exception:
        return False


def remove(path):
    """Remove files/directories. Supports wildcards."""

    try:

        if not path:
            return False

        wildcard = _has_wildcard(path)

        if wildcard:
            targets = glob.glob(path)
        else:
            targets = [path]

        # No matches or missing path is successful.
        if not targets:
            return True

        success = True

        for target in targets:

            target = _normalize(target)

            if not _exists(target):
                continue

            if not _is_safe_delete(target):
                success = False
                continue

            if not _delete_raw(target):
                success = False

        return success

    except Exception:
        return False
