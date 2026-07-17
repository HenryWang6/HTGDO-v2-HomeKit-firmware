#! /bin/sh -

while test $# -gt 0
do
    case "$1" in
        -v) VERBOSE="-vvv"
            ;;
        upload) pio run -t upload -e htgdo_v2_esp32
            ;;
        monitor) pio device monitor -e htgdo_v2_esp32
            ;;
        run) pio run -e htgdo_v2_esp32 $VERBOSE
            ;;
        test)
            python3 -m unittest discover -s tests -p 'test_*.py' -v || exit 1
            node --test tests/test_release_contract.js || exit 1
            (cd lib/secplus && python3 -m unittest test_secplus.py) || exit 1
            ;;
        *) echo "usage: x.sh [-v] <upload|monitor|run|test>"
            exit 1
            ;;
    esac
    shift
done

exit 0
