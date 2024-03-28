import ftReact			from "../ft_react";
import { apiClient }	from "../api/api_client";
import BarLayout 		from "../components/barlayout";
import {
	C_PROFILE_HEADER,
	C_PROFILE_USERNAME
}						from "../conf/content_en";
import Alert from "../components/alert";

const CreateGame = (props) => {
	const createGame = async () => {
		const data = await apiClient.post("/games");
		await props.updateGames();
		props.route("/pong", {game_id: data.id});
	}
	return (
		<button
			className="btn btn-outline-primary mb-3"
			onClick={createGame}
		>
			Create new game
		</button>
	);
}

const DeleteIcon = () => (
		<svg
			xmlns="http://www.w3.org/2000/svg"
			width="16"
			height="16"
			fill="currentColor"
			class="bi bi-trash3"
			viewBox="0 0 16 16"
		>
			<path
				d="M6.5 1h3a.5.5 0 0 1 .5.5v1H6v-1a.5.5 0 0 1 .5-.5M11 2.5v-1A1.5 1.5 0 0 0 9.5 0h-3A1.5 1.5 0 0 0 5 1.5v1H1.5a.5.5 0 0 0 0 1h.538l.853 10.66A2 2 0 0 0 4.885 16h6.23a2 2 0 0 0 1.994-1.84l.853-10.66h.538a.5.5 0 0 0 0-1zm1.958 1-.846 10.58a1 1 0 0 1-.997.92h-6.23a1 1 0 0 1-.997-.92L3.042 3.5zm-7.487 1a.5.5 0 0 1 .528.47l.5 8.5a.5.5 0 0 1-.998.06L5 5.03a.5.5 0 0 1 .47-.53Zm5.058 0a.5.5 0 0 1 .47.53l-.5 8.5a.5.5 0 1 1-.998-.06l.5-8.5a.5.5 0 0 1 .528-.47M8 4.5a.5.5 0 0 1 .5.5v8.5a.5.5 0 0 1-1 0V5a.5.5 0 0 1 .5-.5"
			/>
		</svg>
)

const GameCard = (props) => {
	const me = JSON.parse(localStorage.getItem("me"));
	return (
		<div className="card mb-2" style="width: 18rem;">
			<ul className="list-group list-group-flush">
				<li className="list-group-item d-inline-flex align-items-baseline">
					{props.data.players[0]}
					{props.data.players[0] === me.username &&
						<button
							className="btn d-inline p-0 ms-auto"
							onClick={async ()=>{
								await apiClient.delete("/games", {game_id: props.data.id});
								await props.updateGames();
							}}
						>
							<DeleteIcon/>
						</button>
					}
						<button
							className="btn d-inline p-0 ms-auto"
							onClick={()=>{
								props.route("/pong", {game_id: props.data.id});
							}}
						>
							JOIN
						</button>
				</li>
			</ul>
		</div>
	);
}

const Games = (props) => {
	const [games, setGames] = ftReact.useState(null);
	const [error, setError] = ftReact.useState("");
	const getGames = async () => {
		let data = await apiClient.get("/games", {type: "paused", me: true});
		if (data.length)
			props.route("/pong", {game_id: data[0].id});
		data = await apiClient.get("/games", {type: "pending"});
		if (data.error)
			setError(data.error);
		else if (data && (!games || (games && data.length != games.length)))
			setGames(data);
	};
	if (!games && !error)
		getGames();
	//ftReact.useEffect(()=>{
	//	if (!games && !error)
	//		getGames();
	//},[games]);
	return (
		<BarLayout route={props.route}>
			<CreateGame route={props.route} updateGames={getGames}/>
			{
				games
					? games.map(game => <GameCard route={props.route} data={game} updateGames={getGames}/>)
					: error
						? <Alert msg={error}/>
						: (
							<div className="spinner-grow" role="status">
								<span className="visually-hidden">Loading...</span>
				  			</div>
						)
			}
		</BarLayout>
	);
}

export default Games;