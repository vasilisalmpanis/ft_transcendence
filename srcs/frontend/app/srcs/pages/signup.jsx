import ftReact		from "../ft_react/index.js";
import { apiClient }	from "../api/api_client.js";
import Layout		from "../components/layout.jsx";
import {
	C_SIGNIN_PASS,
	C_SIGNIN_USERNAME,
	C_SIGNUP_BUTTON,
	C_SIGNUP_EMAIL,
	C_SIGNUP_HEADER,
	C_SIGNUP_SIGNIN,
}					from "../conf/content_en.js";
import Alert from "../components/alert.jsx";

const Signup = (props) => {
	const [error, setError] = ftReact.useState("");
	const [username, setUsername] = ftReact.useState("");
	const [pass, setPass] = ftReact.useState("");
	const [email, setEmail] = ftReact.useState("");
	const sendData = async () => {
		const resp = await apiClient.post("/users", {username: username, password: pass, email: email});
		if (resp.error)
			setError(resp.error);
		else
			props.route("/signin");
	};
	return (
		<Layout>
			<h1>{C_SIGNUP_HEADER}</h1>
			<form
				onSubmit={(event)=>{
					event.preventDefault();
					sendData();
				}}
				className="mt-3"
			>
				<div className="mb-3">
					<input
						placeholder={C_SIGNIN_USERNAME}
						className="form-control"
						onChange={(event)=>setUsername(event.target.value)}
						required
					/>
				</div>
				<div className="mb-3">
					<input
						placeholder={C_SIGNIN_PASS}
						type="password"
						className="form-control"
						onChange={(event)=>setPass(event.target.value)}
						required
					/>
				</div>
				<div className="mb-3">
					<input
						placeholder={C_SIGNUP_EMAIL}
						type="email"
						className="form-control"
						onChange={(event)=>setEmail(event.target.value)}
						required
					/>
				</div>
				<div className="mb-3">
					<button
						type="submit"
						className="btn btn-primary w-100"
						>
						{C_SIGNUP_BUTTON}
					</button>
				</div>
				{error && <Alert msg={error}/>}
				<div className="mb-3 mt-5">
					<button
						type="submit"
						className="btn btn-outline-primary w-100"
						onClick={()=>props.route("/signin")}
					>
						{C_SIGNUP_SIGNIN}
					</button>
				</div>
			</form>
		</Layout>
	);
};

export default Signup;