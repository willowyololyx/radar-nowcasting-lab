"""Run this companion's Python-only notebook in-process, without a Jupyter server."""
import argparse
import os
from pathlib import Path

import nbformat
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-repo', type=Path, required=True)
    args = parser.parse_args()
    source = args.source_repo.expanduser().resolve()
    sample = source / 'module2-irene-nowcasting/examples/sample_data.nc'
    if not sample.is_file():
        parser.error(f'Official sample not found: {sample}')
    root = Path(__file__).resolve().parents[1]
    notebook = root / 'notebooks/01_local_sample_audit.ipynb'
    os.environ['IT4LIA_REPO'] = str(source)
    os.chdir(root)
    nb = nbformat.read(notebook, as_version=4)
    shell = InteractiveShell.instance()
    count = 0
    for cell in nb.cells:
        if cell.cell_type != 'code':
            continue
        count += 1
        with capture_output() as captured:
            result = shell.run_cell(cell.source, store_history=False)
        cell.execution_count = count
        cell.outputs = []
        for stream_name, value in [('stdout', captured.stdout), ('stderr', captured.stderr)]:
            if value:
                cell.outputs.append(nbformat.v4.new_output('stream', name=stream_name, text=value))
        for rich in captured.outputs:
            cell.outputs.append(nbformat.v4.new_output('display_data', data=rich.data, metadata=rich.metadata))
        if not result.success:
            error = result.error_before_exec or result.error_in_exec
            raise RuntimeError(f'Notebook failed at code cell {count}: {error}\n{captured.stdout}\n{captured.stderr}') from error
    nb.metadata['execution_method'] = 'Sequential IPython in-process execution; no Jupyter server'
    nbformat.validate(nb)
    nbformat.write(nb, notebook)
    print(f'Executed {count} code cells; reports/ and figures/ contain the outputs.')


if __name__ == '__main__':
    main()
