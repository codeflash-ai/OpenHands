# -*- coding: utf-8 -*-

import os.path
import subprocess
import tempfile
from contextlib import ExitStack

from .exceptions import HunkApplyException, SubprocessException
from .patch import Change, diffobj
from .snippets import remove, which


def _apply_diff_with_subprocess(
    diff: diffobj, lines: list[str], reverse: bool = False
) -> tuple[list[str], list[str] | None]:
    """Applies a diff to a list of lines."""
    # Find the `patch` executable in the system path
    patchexec = which('patch')
    if not patchexec:
        raise SubprocessException('cannot find patch program', code=-1)

    tempdir = tempfile.gettempdir()

    # Create temporary file paths
    filepath_base = os.path.join(tempdir, 'wtp-' + str(hash(diff.header)))
    oldfilepath = filepath_base + '.old'
    newfilepath = filepath_base + '.new'
    rejfilepath = filepath_base + '.rej'
    patchfilepath = filepath_base + '.patch'

    with ExitStack() as stack:
        oldfile = stack.enter_context(open(oldfilepath, 'w'))
        patchfile = stack.enter_context(open(patchfilepath, 'w'))

        oldfile.write('\n'.join(lines) + '\n')
        patchfile.write(diff.text)

        args = [
            patchexec,
            '--reverse' if reverse else '--forward',
            '--quiet',
            '--no-backup-if-mismatch',
            '-o',
            newfilepath,
            '-i',
            patchfilepath,
            '-r',
            rejfilepath,
            oldfilepath,
        ]
        
        ret = subprocess.call(args)

        # Read new file content
        with open(newfilepath) as newfile:
            lines = newfile.read().splitlines()

        try:
            with open(rejfilepath) as rejfile:
                rejlines = rejfile.read().splitlines()
        except IOError:
            rejlines = None

    # Clean up temporary files
    map(remove, [oldfilepath, newfilepath, rejfilepath, patchfilepath])

    # Ensure all files are cleaned up before raising an exception
    if ret != 0:
        raise SubprocessException('patch program failed', code=ret)

    return lines, rejlines


def _reverse(changes: list[Change]) -> list[Change]:
    def _reverse_change(c: Change) -> Change:
        return c._replace(old=c.new, new=c.old)

    return [_reverse_change(c) for c in changes]


def apply_diff(
    diff: diffobj, text: str | list[str], reverse: bool = False, use_patch: bool = False
) -> list[str]:
    lines = text.splitlines() if isinstance(text, str) else list(text)

    if use_patch:
        lines, _ = _apply_diff_with_subprocess(diff, lines, reverse)
        return lines

    n_lines = len(lines)

    changes = _reverse(diff.changes) if reverse else diff.changes
    # check that the source text matches the context of the diff
    for old, new, line, hunk in changes:
        # might have to check for line is None here for ed scripts
        if old is not None and line is not None:
            if old > n_lines:
                raise HunkApplyException(
                    'context line {n}, "{line}" does not exist in source'.format(
                        n=old, line=line
                    ),
                    hunk=hunk,
                )
            if lines[old - 1] != line:
                # Try to normalize whitespace by replacing multiple spaces with a single space
                # This helps with patches that have different indentation levels
                normalized_line = ' '.join(line.split())
                normalized_source = ' '.join(lines[old - 1].split())
                if normalized_line != normalized_source:
                    raise HunkApplyException(
                        'context line {n}, "{line}" does not match "{sl}"'.format(
                            n=old, line=line, sl=lines[old - 1]
                        ),
                        hunk=hunk,
                    )

    # for calculating the old line
    r = 0
    i = 0

    for old, new, line, hunk in changes:
        if old is not None and new is None:
            del lines[old - 1 - r + i]
            r += 1
        elif old is None and new is not None:
            lines.insert(new - 1, line)
            i += 1
        elif old is not None and new is not None:
            # Sometimes, people remove hunks from patches, making these
            # numbers completely unreliable. Because they're jerks.
            pass

    return lines
