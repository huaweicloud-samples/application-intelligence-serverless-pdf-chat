import { Outlet } from "react-router-dom";
import Navigation from "../components/Navigation";
import Footer from "../components/Footer";

// The layout is a static shell; user identity travels with each API request.
const Layout: React.FC = () => {
  return (
    <div className="flex flex-col min-h-screen">
      <div>
        <Navigation />
        <div className="container mt-6 mb-6">
          <Outlet />
        </div>
      </div>
      <Footer />
    </div>
  );
};

export default Layout;
