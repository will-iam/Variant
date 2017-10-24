
parser = argparse.ArgumentParser(description="Regression test", prefix_chars='-')
parser.add_argument("project_name", type = str, help = "Name of scheme")
parser.add_argument("-c", type = str, help = "Case to test")
parser.add_argument("--gdb", action='store_true',
        default=False, help = "Debug mode")
args = parser.parse_args()

project_name = args.project_name
comp = 'mpi'
mode = 'debug'
precision = 'double'
std = 'c++11'
bool_compile = True
gdb = args.gdb

this_dir = os.path.split(os.path.abspath(__file__))[0]
tmp_dir = config.tmp_dir

case_dir = os.path.join("case", project_name)

test = dict()
test['nSDD'] = (1, 1)
test['nSDS'] = 1
test['nThreads'] = 1
test['SDSgeom'] = 'line'

# Launch test
current_test_path, _, _ = launch_test(this_dir, tmp_dir,
    project_name, cn, comp, mode, precision, std, bool_compile,
    test, gdb)

# Compare to analytical solution
