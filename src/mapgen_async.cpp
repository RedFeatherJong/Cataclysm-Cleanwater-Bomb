#include "mapgen_async.h"

#include <mutex>
#include <utility>
#include <vector>

#include "auto_note.h"
#include "map_extras.h"
#include "options.h"
#include "overmapbuffer.h"

namespace mapgen_defer
{

namespace
{

std::mutex                     g_autonote_mutex;
std::vector<string_id<map_extra>> g_pending_extras;

// TODO: Lua hooks will be added when CCB ports Lua integration

} // namespace

void drain()
{
    // No-op: Lua hooks not yet ported.
}

void push_autonote( const tripoint_abs_omt & /*pos*/,
                    const string_id<map_extra> & /*extra*/ )
{
    // No-op: auto_note is main-thread-only.
    // Deferred autonote logic will be hooked in when worker mapgen is enabled.
}

} // namespace mapgen_defer
