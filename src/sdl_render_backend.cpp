#include "sdl_render_backend.h"

#if defined(TILES)

#include "cata_tiles.h"
#include "output.h"

sdl_render_backend::sdl_render_backend() = default;
sdl_render_backend::~sdl_render_backend() = default;

bool sdl_render_backend::present()
{
    // Stage 4A: shell — the backend exists but is not wired into any call
    // path yet.  present_turn() still calls ui_manager::redraw() directly.
    // In 4B this will forward to tiles->draw(…).
    return true;
}

void sdl_render_backend::resize( int, int )
{
    // Stage 4A: no-op.  4B will notify tiles of the new viewport size.
}

void sdl_render_backend::flush()
{
    // Forward to the existing SDL present call.  Both the old path and the
    // backend path share the same SDL window, so refresh_display() is safe
    // to call from either side.
    refresh_display();
}

const char *sdl_render_backend::name() const
{
    return "sdl";
}

// Stage 4A placeholder — returns nullptr.  In 4B this will return
// std::make_unique<sdl_render_backend>() once SDL init timing is resolved.
std::unique_ptr<render_backend> create_render_backend()
{
    return nullptr;
}

#endif // TILES
