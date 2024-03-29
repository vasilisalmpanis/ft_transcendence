import ftReact from "../ft_react";

const Layout = ({children, ...rest}) => {
	return (
		<div className="
			container-md
			text-center
			d-flex
			flex-column
			mb-3
			justify-content-center
			align-items-center
			h-100
		">
			{children}
		</div>
	);
};

export default Layout;