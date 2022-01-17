import carball

analysis_manager = carball.analyze_replay_file('replays/fa63ffda-180a-4166-a952-f87cd5a82e7c.replay')

print(analysis_manager.get_json_data())
