#include <stdio.h>
#include <Python.h>

#ifdef _WIN32
# define WIN32_LEAN_AND_MEAN
# include <windows.h>
#endif
#include <locale.h>

// https://stackoverflow.com/a/12648993
#define STR_VER_(x) #x
#define STR_VER(x) STR_VER_(x)
#ifndef CX_DIST_VER
#define CX_DIST_VER local
#endif
#define set_chimerax_dist_ver(ver) PyModule_AddStringConstant(cx_module, "_CHIMERAX_C_DIST_VERSION", STR_VER(CX_DIST_VER) "-" ver)

/*
 * Mimic:
 *
 *	python -I [-X faulthandler] -m ChimeraX_main.py app-args
 */

static wchar_t* extra[] = {
	L"-I",
#if 0
	// TODO: Probably the right thing to do, but needs discussing
	L"-X",
	L"utf8",
#endif
#ifndef _WIN32
	// Works when started from cygwin shell, but not when
	// double-clicked upon, nor from command prompt shell
	L"-X",
	L"faulthandler",
#endif
	L"-m",
	L"chimerax.core",
};
static const int ec = sizeof(extra) / sizeof (extra[0]);

static wchar_t* debug_extra[] = {
	L"-X",
	L"dev",
/* Too much output from import timing for debugging.
	L"-X",
	L"importtime",
 */
};
static const int debug_ec = sizeof(debug_extra) / sizeof (debug_extra[0]);

/*
 * Make Nvidia Optimus GPU switching choose high performance graphics.
 * http://developer.download.nvidia.com/devzone/devcenter/gamegraphics/files/OptimusRenderingPolicies.pdf
 */
#ifdef _WIN32
_declspec(dllexport) DWORD NvOptimusEnablement = 0x00000001;
#endif

int
app_main(int argc, wchar_t** wargv)
{
	int debug = 0;
	for (int i = 1; i < argc; ++i) {
		if (wcscmp(wargv[i], L"--debug") == 0) {
			debug = 1;
			break;
		}
	}
	int new_argc = argc + ec + debug * debug_ec;
	wchar_t** new_argv = (wchar_t**) malloc((new_argc + 1) * sizeof (wchar_t*));
	if (new_argv == NULL) {
		fprintf(stderr, "out of memory\n");
		return 123;
	}
	int ac = 0;
	new_argv[ac++] = wargv[0];
	if (debug) {
		for (int i = 0; i < debug_ec; ++i)
			new_argv[ac++] = debug_extra[i];
	}
	for (int i = 0; i < ec; ++i)
		new_argv[ac++] = extra[i];
	for (int i = 1; i < argc; ++i)
		new_argv[ac++] = wargv[i];
	assert(ac == new_argc);
	new_argv[ac] = NULL;
	// On launch, inject version information into the ChimeraX binary.
	Py_Initialize();
	PyObject* cx_module = PyImport_ImportModule("chimerax");
#ifdef techpreview
	set_chimerax_dist_ver("techpreview");
#else
#ifdef candidate
	set_chimerax_dist_ver("rc");
#else
#ifdef daily
	set_chimerax_dist_ver("daily");
#else
#ifdef production
	set_chimerax_dist_ver("");
#else
	set_chimerax_dist_ver("developer");
#endif
#endif
#endif
#endif
	PyModule_AddStringConstant(cx_module, "_CHIMERAX_C_DIST_BUILD_DATE", __DATE__);
	int result = Py_Main(new_argc, new_argv);
	free(new_argv);
	Py_Finalize();
	return result;
}
