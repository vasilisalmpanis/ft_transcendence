import ftReact		from "../ft_react";
import Layout from "./layout";


const BarLayout = (props) => {
	return (
		<div className="h-100">
			<nav className="navbar bg-body-tertiary">
			  	<div className="container-fluid">
				  	<button
						onClick={() => props.route("/")}
						className="btn btn-outline-secondary me-3"
					>
						PONG 42
					</button>
					<button
						onClick={() => props.route("/me")}
						className="rounded-circle btn btn-outline-secondary me-3 ms-auto"
					>
						P
					</button>
			  	</div>
			</nav>
			<Layout>
				{props.children}
			</Layout>
		</div>
	)
};

export default BarLayout; 