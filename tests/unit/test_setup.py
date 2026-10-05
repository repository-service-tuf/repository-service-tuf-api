def test_setup(monkeypatch):
    import setuptools
    import pretend

    mocked_setup = pretend.call_recorder(lambda **kw: None)
    monkeypatch.setattr(setuptools, "setup", mocked_setup)

    import setup

    assert len(mocked_setup.calls) == 1
    assert mocked_setup.calls[0].kwargs["name"] == "repository-service-tuf-api"

