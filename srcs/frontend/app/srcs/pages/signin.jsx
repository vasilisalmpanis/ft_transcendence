import ftReact			from "../ft_react/index.js";
import { apiClient }	from "../api/api_client.js";
import Layout			from "../components/layout.jsx";
import {
	C_SIGNIN_BUTTON,
	C_SIGNIN_HEADER,
	C_SIGNIN_INTRA,
	C_SIGNIN_INTRA_ENDPOINT,
	C_SIGNIN_PASS,
	C_SIGNIN_SIGNUP,
	C_SIGNIN_USERNAME
}						from "../conf/content_en.js";
import Alert from "../components/alert.jsx";


const Signin = (props) => {
	const [error, setError] = ftReact.useState("");
	if (location.search.length) {
		const handleQuery = async () => {
			let queryDict = new URLSearchParams(location.search);
			if (queryDict.has("access_token")) {
				const res = apiClient.authorize({
					access_token: queryDict.get("access_token"),
					refresh_token: queryDict.get("refresh_token")
				});
				if (res.error)
					setError(res.error);
				else {
					queryDict.delete("access_token");
					queryDict.delete("refresh_token");
					props.route("/");
				}
			}
		}
		handleQuery();
	}
	const submit = async (event) => {
		event.preventDefault();
		const username = event.target[0].value;
		const password = event.target[1].value;
		const resp = await apiClient.authorize({
			username: username,
			password: password
		});
		if (resp)
			resp.error ? setError(resp.error) : props.route("/");
	};
	return (
		<Layout>
			<div>
				<h1>{C_SIGNIN_HEADER}</h1>
				<form
					onSubmit={submit}
					className="mt-3"
				>
					<div className="mb-3">
						<input
							placeholder={C_SIGNIN_USERNAME}
							className="form-control"
							required
						/>
					</div>
					<div className="mb-3">
						<input
							placeholder={C_SIGNIN_PASS}
							type="password"
							className="form-control"
							required
						/>
					</div>
					<div className="mb-3">
						<button
							type="submit"
							className="btn btn-primary w-100"
						>
							{C_SIGNIN_BUTTON}
						</button>
					</div>
					{error && <Alert msg={error}/>}
				</form>
				<div className="mb-3 mt-5">
					<button
						type="submit"
						className="btn btn-outline-primary w-100"
						onClick={()=>props.route("/signup")}
					>
						{C_SIGNIN_SIGNUP}
					</button>
				</div>
				<div className="mb-3">
					<a
						type="submit"
						className="btn btn-outline-primary w-100"
						href={C_SIGNIN_INTRA_ENDPOINT}
					>
						{C_SIGNIN_INTRA}
					</a>
				</div>
			</div>
		</Layout>
	);
};

export default Signin;
