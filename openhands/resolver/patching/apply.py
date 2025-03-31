# -*- coding: utf-8 -*-

import os.path
import subprocess
import tempfile
from tempfile import NamedTemporaryFile

from .exceptions import HunkApplyException, SubprocessException
from .patch import Change, diffobj
from .snippets import remove, which


def _apply_diff_with_subprocess(
    diff: diffobj, lines: list[str], reverse: bool = False
) -> tuple[list[str], list[str] | None]:
    # call out to patch program
    patchexec = which('patch')
    if not patchexec:
        raise SubprocessException('cannot find patch program', code=-1)

    with NamedTemporaryFile('w+', delete=False) as old_file, \
         NamedTemporaryFile('w+', delete=False) as patch_file, \
         NamedTemporaryFile('r+', delete=False) as new_file, \
         NamedTemporaryFile('r+', delete=False) as rej_file:

        old_file.write('\n'.join(lines) + '\n')
        oldfilepath = old_file.name

        patch_file.write(diff.text)
        patchfilepath = patch_file.name
       
        args = [
            patchexec,
            '--reverse' if reverse else '--forward',
            '--quiet',
            '--no-backup-if-mismatch',
            '-o',
            new_file.name,
            '-i',
            patchfilepath,
            '-r',
            rej_file.name,
            oldfilepath,
        ]
        ret = subprocess.call(args)

        # Read new_file contents
        new_file.seek(0)
        lines = new_file.read().splitlines()

        try:
            rej_file.seek(0)
            rejlines = rej_file.read().splitlines()
        except IOError:
            rejlines = None

    # Clean up temporary files
    remove(oldfilepath)
    remove(patchfilepath)
    remove(new_file.name)
    remove(rej_file.name)

    # Check and raise exception after file clean-up
    if ret != 0:
        raise SubprocessException('patch program failed', code=ret)

    return lines, rejlines


def _reverse(changes: list[Change]) -> list[Change]:
    return [c._replace(old=c.new, new=c.old) for c in changes]


def apply_diff(
    diff: diffobj, text: str | list[str], reverse: bool = False, use_patch: bool = False
) -> list[str]:
    lines = text.splitlines() if isinstance(text, str) else list(text)

    if use_patch:
        lines, _ = _apply_diff_with_subprocess(diff, lines, reverse)
        return lines

    n_lines = len(lines)

    changes = _reverse(diff.changes) if reverse else diff.changes

    # Validate source text with context lines
    for old, new, line, hunk in changes:
        if old is not None and line is not None:
            if old > n_lines:
                raise HunkApplyException(
                    f'context line {old}, "{line}" does not exist in source', hunk=hunk
                )
            if lines[old - 1] != line:
                normalized_line = ' '.join(line.split())
                normalized_source = ' '.join(lines[old - 1].split())
                if normalized_line != normalized_source:
                    raise HunkApplyException(
                        f'context line {old}, "{line}" does not match "{lines[old - 1]}"', hunk=hunk
                    )

    # Efficient change application
    r = 0
    i = 0
    for old, new, line, hunk in changes:
        if old is not None and new is None:
            del lines[old - 1 - r + i]
            r += 1
        elif old is None and new is not None:
            lines.insert(new - 1, line)
            i += 1

    return lines
