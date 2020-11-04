import pytest

from asynctest.mock import call, CoroutineMock

from google.api_core.exceptions import FailedPrecondition

from google.cloud.pubsublite.cloudpubsub.internal.client_multiplexer import (
    AsyncClientMultiplexer,
)

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


class Client:
    pass


@pytest.fixture()
def client_factory():
    return CoroutineMock()


@pytest.fixture()
def client_closer():
    return CoroutineMock()


@pytest.fixture()
def multiplexer(client_closer):
    return AsyncClientMultiplexer(client_closer)


async def test_create(
    multiplexer: AsyncClientMultiplexer[int, Client], client_closer, client_factory
):
    client1 = Client()
    client2 = Client()
    async with multiplexer:
        client_factory.return_value = client1
        assert await multiplexer.create_or_fail(1, client_factory) is client1
        client_factory.assert_has_calls([call()])
        client_factory.return_value = client2
        assert await multiplexer.get_or_create(1, client_factory) is client1
        with pytest.raises(FailedPrecondition):
            await multiplexer.create_or_fail(1, client_factory)
        assert await multiplexer.get_or_create(2, client_factory) is client2
        client_factory.assert_has_calls([call(), call()])
        with pytest.raises(FailedPrecondition):
            await multiplexer.create_or_fail(2, client_factory)
    client_closer.assert_has_calls([call(client1), call(client2)], any_order=True)


async def test_recreate(
    multiplexer: AsyncClientMultiplexer[int, Client], client_closer, client_factory
):
    client1 = Client()
    client2 = Client()
    async with multiplexer:
        client_factory.return_value = client1
        assert await multiplexer.create_or_fail(1, client_factory) is client1
        client_factory.assert_has_calls([call()])
        client_factory.return_value = client2
        await multiplexer.try_erase(1, client2)
        client_closer.assert_has_calls([])
        await multiplexer.try_erase(1, client1)
        client_closer.assert_has_calls([call(client1)])
        assert await multiplexer.create_or_fail(1, client_factory) is client2
    client_closer.assert_has_calls([call(client1), call(client2)])