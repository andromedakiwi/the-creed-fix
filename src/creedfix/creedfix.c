/*
 * The Creed (1999) - Unofficial Patch v2 - creedfix (dinput.dll proxy)
 * by Andromeda Kiwi + Claude - MIT License
 *
 * Creed.exe imports DINPUT.dll. Windows loads this dinput.dll from the game
 * folder first; at load time it checks that Creed.exe is the original
 * v1.6 build 160 and applies the fixes in memory. DirectInput calls are
 * forwarded to the real dinput.dll in the system folder.
 *
 * Nothing is written to Creed.exe on disk. See docs/TECHNICAL.md for every
 * address used here.
 */
#include <windows.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>

/* ------------------------------------------------------------------ */
/* State shared with the assembly stubs                                */
/* ------------------------------------------------------------------ */
volatile DWORD g_inactive = 0;          /* 1 while the game window is not the active app */
static char g_log_path[MAX_PATH];
static char g_game_dir[MAX_PATH];
static int  g_patch_ok = 0;
static char g_fail_reason[256];

static void log_line(const char *fmt, ...)
{
    FILE *f = fopen(g_log_path, "a");
    if (!f) return;
    va_list ap;
    va_start(ap, fmt);
    vfprintf(f, fmt, ap);
    va_end(ap);
    fputc('\n', f);
    fclose(f);
}

/* ------------------------------------------------------------------ */
/* Forwarding to the real dinput.dll                                   */
/* ------------------------------------------------------------------ */
static HMODULE g_real;

static FARPROC real_proc(const char *name)
{
    if (!g_real) {
        char path[MAX_PATH];
        UINT n = GetSystemDirectoryA(path, MAX_PATH);   /* SysWOW64 for a 32-bit process */
        if (n == 0 || n > MAX_PATH - 16) return NULL;
        strcat(path, "\\dinput.dll");
        g_real = LoadLibraryA(path);
        if (!g_real) { log_line("ERROR: could not load %s", path); return NULL; }
    }
    return GetProcAddress(g_real, name);
}

static void warn_once(void)
{
    static int shown = 0;
    if (shown || g_patch_ok) return;
    shown = 1;
    char msg[512];
    snprintf(msg, sizeof msg,
             "The Creed unofficial patch could not be applied:\n\n%s\n\n"
             "The game will run without the fixes. Details in creedfix.log.",
             g_fail_reason);
    MessageBoxA(NULL, msg, "The Creed - unofficial patch", MB_OK | MB_ICONWARNING);
}

typedef HRESULT (WINAPI *DICreateA)(HINSTANCE, DWORD, void **, void *);
typedef HRESULT (WINAPI *DICreateEx)(HINSTANCE, DWORD, const GUID *, void **, void *);

__declspec(dllexport) HRESULT WINAPI DirectInputCreateA(HINSTANCE h, DWORD v, void **o, void *u)
{
    warn_once();
    DICreateA f = (DICreateA)real_proc("DirectInputCreateA");
    return f ? f(h, v, o, u) : E_FAIL;
}
__declspec(dllexport) HRESULT WINAPI DirectInputCreateW(HINSTANCE h, DWORD v, void **o, void *u)
{
    DICreateA f = (DICreateA)real_proc("DirectInputCreateW");
    return f ? f(h, v, o, u) : E_FAIL;
}
__declspec(dllexport) HRESULT WINAPI DirectInputCreateEx(HINSTANCE h, DWORD v, const GUID *r, void **o, void *u)
{
    DICreateEx f = (DICreateEx)real_proc("DirectInputCreateEx");
    return f ? f(h, v, r, o, u) : E_FAIL;
}
__declspec(dllexport) HRESULT WINAPI DllCanUnloadNow(void) { return S_FALSE; }
__declspec(dllexport) HRESULT WINAPI DllGetClassObject(const CLSID *c, const IID *i, void **o)
{
    typedef HRESULT (WINAPI *F)(const CLSID *, const IID *, void **);
    F f = (F)real_proc("DllGetClassObject");
    return f ? f(c, i, o) : E_FAIL;
}

/* ------------------------------------------------------------------ */
/* Fixes implemented in C                                              */
/* ------------------------------------------------------------------ */

/* Replaces 0x00405CF0 (CD drive search). Hybrid No-CD: if the game folder has
 * cd1\Data\data.v00 (disc 1) or cd2\Data\Data.v01 (disc 2), use that folder as
 * the CD root (string at 0x004F5268, 256 bytes), else run the original search. */
extern int cd_original(void);          /* trampoline in asm below */

int __cdecl cd_find(void)
{
    BYTE disc = *(volatile BYTE *)0x4F5368;
    const char *sub  = (disc == 2) ? "cd2\\" : "cd1\\";
    const char *test = (disc == 2) ? "Data\\Data.v01" : "Data\\data.v00";
    char root[MAX_PATH], file[MAX_PATH];
    snprintf(root, sizeof root, "%s%s", g_game_dir, sub);
    snprintf(file, sizeof file, "%s%s", root, test);
    if (strlen(root) < 200 && GetFileAttributesA(file) != INVALID_FILE_ATTRIBUTES) {
        strcpy((char *)0x4F5268, root);
        return 1;
    }
    return cd_original();
}

/* Replaces 0x00431BB0 (music volume through the CD-audio mixer line, absent on
 * modern PCs): set ogg-winmm's CD volume instead. vol is 0..0xFFFF. */
void __cdecl music_volume(DWORD vol)
{
    typedef UINT (WINAPI *AUXSET)(UINT, DWORD);
    static AUXSET aux;
    if (!aux) {
        HMODULE w = GetModuleHandleA("winmm.dll");   /* the game folder's winmm.dll (ogg-winmm) */
        if (w) aux = (AUXSET)GetProcAddress(w, "auxSetVolume");
        if (!aux) return;
    }
    vol &= 0xFFFF;
    aux(0, vol | (vol << 16));
}

/* ------------------------------------------------------------------ */
/* Fixes that need exact register/stack handling: naked asm stubs      */
/* (game addresses are absolute: Creed.exe has no relocations and      */
/*  always loads at 0x00400000; we check that before patching)         */
/* ------------------------------------------------------------------ */
#define JMPABS(a) "push " #a "\n ret\n"

/* trampoline: the 6 bytes replaced at 0x00405CF0, then continue the original */
__attribute__((naked)) int cd_original(void)
{
    __asm__(
        "sub esp, 0x20c\n"
        JMPABS(0x405cf6)
    );
}

/* 0x00405CF0 -> calls into C */
__attribute__((naked)) void stub_cd(void)
{
    __asm__(
        "jmp _cd_find\n"
    );
}

/* 0x00425670: clip every dirty rectangle (list 0x4B689C, count 0x4B6898) to
 * 640x480 before the background restore (BltFast) and the depth copy use it. */
__attribute__((naked)) void stub_clip(void)
{
    __asm__(
        "movzx ecx, word ptr ds:0x4b6898\n"
        "mov edx, 0x4b689c\n"
        "xor eax, eax\n"
        "1: test ecx, ecx\n"
        " je 9f\n"
        " cmp dword ptr [edx], eax\n"
        " jge 2f\n"
        " mov dword ptr [edx], eax\n"
        "2: cmp dword ptr [edx+4], eax\n"
        " jge 3f\n"
        " mov dword ptr [edx+4], eax\n"
        "3: cmp dword ptr [edx+8], 0x280\n"
        " jle 4f\n"
        " mov dword ptr [edx+8], 0x280\n"
        "4: cmp dword ptr [edx+12], 0x1e0\n"
        " jle 5f\n"
        " mov dword ptr [edx+12], 0x1e0\n"
        "5: add edx, 16\n"
        " dec ecx\n"
        " jmp 1b\n"
        "9: mov eax, dword ptr ds:0x4f6eec\n"   /* replaced instructions */
        " sub esp, 0xec\n"
        JMPABS(0x42567b)
    );
}

/* 0x0043C7D1, after the registry read: behave as if the Hardware Accelerated
 * data (Scene16) and a full install were registered. */
__attribute__((naked)) void stub_reg(void)
{
    __asm__(
        "mov dword ptr ds:0x4f7234, 1\n"
        "mov byte ptr ds:0x4f5368, 1\n"
        "mov ecx, dword ptr [esp+0x24]\n"      /* replaced instructions */
        "push 0x80\n"
        JMPABS(0x43c7da)
    );
}

/* 0x0043C3FA in the window procedure (esi = msg, edi = wParam):
 * remember WM_ACTIVATEAPP. */
__attribute__((naked)) void stub_wndproc(void)
{
    __asm__(
        "cmp esi, 0x1c\n"
        "jne 1f\n"
        "xor eax, eax\n"
        "test edi, edi\n"
        "sete al\n"
        "mov dword ptr [_g_inactive], eax\n"
        "1: cmp esi, 0x10\n"
        "ja 2f\n"
        JMPABS(0x43c3ff)
        "2:\n"
        JMPABS(0x43c423)
    );
}

/* 0x0042A205: enter the focus-loss pause only while inactive
 * (was: while IDirectDraw4::TestCooperativeLevel fails, which never recovers). */
__attribute__((naked)) void stub_pause_enter(void)
{
    __asm__(
        "cmp dword ptr [_g_inactive], 0\n"
        "je 1f\n"
        JMPABS(0x42a218)
        "1:\n"
        JMPABS(0x42a2a0)
    );
}

/* 0x0042A254: leave the pause when active again; drop the mouse movement made
 * while paused (immediate-mode deltas), then the original restore/reload. */
__attribute__((naked)) void stub_pause_leave(void)
{
    __asm__(
        "cmp dword ptr [_g_inactive], 0\n"
        "je 1f\n"
        JMPABS(0x42a21e)
        "1: mov eax, dword ptr ds:0x4f69fc\n"
        " push 0x4e7bf0\n"
        " push 0x10\n"
        " push eax\n"
        " mov ecx, dword ptr [eax]\n"
        " call dword ptr [ecx+0x24]\n"          /* IDirectInputDevice::GetDeviceState */
        JMPABS(0x42a263)
    );
}

/* 0x00408367: play the startup intro only in single player and when the
 * Configuration checkbox "Intro Videos" ([0x4F5258], Config.dat) is ticked. */
__attribute__((naked)) void stub_intro(void)
{
    __asm__(
        "mov dword ptr ds:0x4f5374, 1\n"       /* replaced instruction */
        "cmp dword ptr ds:0x4bcd90, 0\n"
        "jne 1f\n"
        "cmp dword ptr ds:0x4f5258, 0\n"
        "je 1f\n"
        JMPABS(0x40837a)
        "1:\n"
        JMPABS(0x4083be)
    );
}

/* 0x00431BB0 -> C (cdecl, argument on the stack is untouched) */
__attribute__((naked)) void stub_volume(void)
{
    __asm__("jmp _music_volume\n");
}

/* ------------------------------------------------------------------ */
/* Patching                                                            */
/* ------------------------------------------------------------------ */
typedef struct {
    DWORD addr;           /* VA in Creed.exe */
    const char *orig;     /* original bytes (hex) */
    int len;              /* bytes overwritten */
    void *target;         /* jmp target, or NULL for a plain byte patch */
    const char *bytes;    /* replacement bytes (hex) when target == NULL */
    const char *what;
} PATCH;

static PATCH patches[] = {
    { 0x406D15, "00180000", 4, NULL, "40280000",
      "background buffer caps TEXTURE -> OFFSCREENPLAIN|3DDEVICE (black menus, cursor trails)" },
    { 0x405FC2, "09", 1, NULL, "0a",
      "DirectInput keyboard EXCLUSIVE|BACKGROUND -> NONEXCLUSIVE|BACKGROUND" },
    { 0x405CF0, "81ec0c0200", 5, stub_cd, NULL, "hybrid No-CD (cd1\\ / cd2\\ folders)" },
    { 0x408367, "a190cd4b00c70574534f000100000085c07544", 19, stub_intro, NULL,
      "startup intro follows the 'Intro Videos' option" },
    { 0x425670, "a1ec6e4f0081ecec000000", 11, stub_clip, NULL,
      "clip dirty rectangles to the screen (gameplay crash, edge trails)" },
    { 0x42A205, "a1086a4f00508b10ff526885c00f8488000000", 19, stub_pause_enter, NULL,
      "focus-loss pause driven by WM_ACTIVATEAPP (enter)" },
    { 0x42A254, "a1086a4f00508b08ff516885c075bb", 15, stub_pause_leave, NULL,
      "focus-loss pause driven by WM_ACTIVATEAPP (leave, mouse flush)" },
    { 0x431BB0, "81ec78010000", 6, stub_volume, NULL, "music volume -> ogg-winmm auxSetVolume" },
    { 0x43C3FA, "83fe107724", 5, stub_wndproc, NULL, "window procedure: track WM_ACTIVATEAPP" },
    { 0x43C7D1, "8b4c24246880000000", 9, stub_reg, NULL,
      "no registry needed (Hardware Accelerated, full install)" },
};

static int hexbytes(const char *hex, BYTE *out, int max)
{
    int n = 0;
    while (hex[0] && hex[1] && n < max) {
        unsigned v;
        sscanf(hex, "%2x", &v);
        out[n++] = (BYTE)v;
        hex += 2;
    }
    return n;
}

static int write_mem(void *dst, const void *src, SIZE_T len)
{
    DWORD old;
    if (!VirtualProtect(dst, len, PAGE_EXECUTE_READWRITE, &old)) return 0;
    memcpy(dst, src, len);
    VirtualProtect(dst, len, old, &old);
    FlushInstructionCache(GetCurrentProcess(), dst, len);
    return 1;
}

/* Rename the Configuration checkbox "Intro Attract" -> "Intro Videos " in the
 * in-memory resource (same UTF-16 length, so the dialog template is unchanged). */
static void patch_label(BYTE *base)
{
    IMAGE_NT_HEADERS *nt = (IMAGE_NT_HEADERS *)(base + ((IMAGE_DOS_HEADER *)base)->e_lfanew);
    IMAGE_DATA_DIRECTORY rd = nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_RESOURCE];
    const WCHAR from[] = L"Intro Attract", to[] = L"Intro Videos ";
    SIZE_T n = sizeof from - sizeof(WCHAR);
    BYTE *p = base + rd.VirtualAddress, *end = p + rd.Size - n;
    for (; p < end; p += 2) {
        if (memcmp(p, from, n) == 0) {
            if (write_mem(p, to, n)) log_line("  ok   0x%08lX  Configuration label 'Intro Attract' -> 'Intro Videos'", (unsigned long)(p - base) + 0x400000UL);
            return;
        }
    }
    log_line("  note Configuration label not found (left as is)");
}

static void apply_patches(void)
{
    BYTE *base = (BYTE *)GetModuleHandleA(NULL);
    IMAGE_NT_HEADERS *nt = (IMAGE_NT_HEADERS *)(base + ((IMAGE_DOS_HEADER *)base)->e_lfanew);

    if ((DWORD_PTR)base != 0x400000) {
        snprintf(g_fail_reason, sizeof g_fail_reason, "unexpected load address %p", base);
        log_line("ERROR: %s", g_fail_reason);
        return;
    }
    if (nt->FileHeader.TimeDateStamp != 0x3692CA5C) {
        snprintf(g_fail_reason, sizeof g_fail_reason,
                 "Creed.exe is not the original v1.6 build 160 (timestamp %08lX).\n"
                 "If you used patch v1.x, put back your original Creed.exe "
                 "(Creed.exe.original or your backup).",
                 (unsigned long)nt->FileHeader.TimeDateStamp);
        log_line("ERROR: %s", g_fail_reason);
        return;
    }

    /* verify every site first: all or nothing */
    int i, n = sizeof patches / sizeof patches[0];
    for (i = 0; i < n; i++) {
        BYTE want[64];
        int len = hexbytes(patches[i].orig, want, sizeof want);
        if (len != patches[i].len || memcmp((void *)patches[i].addr, want, len) != 0) {
            snprintf(g_fail_reason, sizeof g_fail_reason,
                     "Creed.exe does not match the original at 0x%08lX.\n"
                     "If you used patch v1.x, put back your original Creed.exe.",
                     (unsigned long)patches[i].addr);
            log_line("ERROR: %s", g_fail_reason);
            return;
        }
    }
    for (i = 0; i < n; i++) {
        BYTE buf[64];
        int len = patches[i].len;
        if (patches[i].target) {
            DWORD rel = (DWORD)patches[i].target - (patches[i].addr + 5);
            buf[0] = 0xE9;
            memcpy(buf + 1, &rel, 4);
            memset(buf + 5, 0x90, len - 5);
        } else {
            hexbytes(patches[i].bytes, buf, sizeof buf);
        }
        if (!write_mem((void *)patches[i].addr, buf, len)) {
            log_line("  FAIL 0x%08lX  %s (VirtualProtect %lu)", (unsigned long)patches[i].addr,
                 patches[i].what, GetLastError());
            snprintf(g_fail_reason, sizeof g_fail_reason, "could not write to Creed.exe memory");
            return;
        }
        log_line("  ok   0x%08lX  %s", (unsigned long)patches[i].addr, patches[i].what);
    }
    patch_label(base);
    g_patch_ok = 1;
}

BOOL WINAPI DllMain(HINSTANCE inst, DWORD reason, LPVOID reserved)
{
    (void)reserved;
    if (reason == DLL_PROCESS_ATTACH) {
        DisableThreadLibraryCalls(inst);
        char exe[MAX_PATH];
        DWORD n = GetModuleFileNameA(NULL, exe, MAX_PATH);
        char *slash = (n && n < MAX_PATH) ? strrchr(exe, '\\') : NULL;
        if (slash) { slash[1] = 0; strcpy(g_game_dir, exe); }
        snprintf(g_log_path, sizeof g_log_path, "%screedfix.log", g_game_dir);
        DeleteFileA(g_log_path);
        log_line("The Creed unofficial patch v2.0 (creedfix dinput.dll) - by Andromeda Kiwi + Claude");
        log_line("Game folder: %s", g_game_dir);
        apply_patches();
        log_line(g_patch_ok ? "All fixes applied." : "Fixes NOT applied - game runs unpatched.");
    }
    return TRUE;
}
