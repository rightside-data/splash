from twisted.internet import defer

class RenderPool(object):
    """A pool of renders. The number of slots determines how many
    renders will be run in parallel, at the most."""

    def __init__(self, slots, get_cache=None, get_proxy_factory=None):
        self.get_cache = get_cache
        self.get_proxy_factory = get_proxy_factory
        self.active = set()
        self.queue = defer.DeferredQueue()
        for n in range(slots):
            self._wait_for_render(None, n)

    def render(self, rendercls, *args):
        extdef = defer.Deferred()
        self.queue.put((rendercls, args, extdef))
        return extdef

    def _wait_for_render(self, _, slot):
        d = self.queue.get()
        d.addCallback(self._start_render)
        d.addBoth(self._wait_for_render, slot)
        return _

    def _start_render(self, (rendercls, args, extdef)):
        render = rendercls(
            get_cache=self.get_cache,
            get_proxy_factory=self.get_proxy_factory
        )
        render.doRequest(*args)
        self.active.add(render)
        d = render.deferred
        d.addBoth(self._close_render, render)
        d.chainDeferred(extdef)
        return d

    def _close_render(self, _, render):
        self.active.remove(render)
        render.close()
        return _
